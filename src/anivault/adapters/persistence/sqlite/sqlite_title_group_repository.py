"""sqlite_title_group_repository.py

TitleGroupRepository SQLite 구현.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sql_queries import GROUP_TMDB_MATCH_UPSERT_SQL
from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.title_groups import (
    TitleGroupListRecord,
    TitleGroupMemberSync,
    TitleGroupSyncBundle,
)
from anivault.domain.services.title_grouping import TitleGroupingInputRow


class SqliteTitleGroupRepository:
    """title_groups·title_group_members 테이블."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 직렬화용 Lock 을 받는다.

        Args:
            self: 저장소.
            conn: 공유 SQLite 연결.
            lock: 메서드 단위 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingInputRow]:
        """parse_cache 가 ok 인 미디어 행을 그룹 입력으로 만든다.

        Args:
            self: 저장소.
            root_id: 루트 ID.

        Returns:
            `TitleGroupingInputRow` 목록.
        """
        sql = """
            SELECT
                m.id,
                c.parsed_title,
                c.parsed_title_normalized,
                c.parsed_year,
                m.sidecar_group_key,
                m.media_kind
            FROM media_files m
            INNER JOIN parse_cache c ON c.media_file_id = m.id
            WHERE m.root_id = ?
              AND m.is_deleted = 0
              AND c.parse_status = 'ok'
            ORDER BY m.id
        """
        with self._lock:
            cur = self._conn.execute(sql, (root_id,))
            rows = cur.fetchall()
            self._conn.commit()
        out: list[TitleGroupingInputRow] = []
        for r in rows:
            sc = r[4]
            out.append(
                TitleGroupingInputRow(
                    media_file_id=int(r[0]),
                    parsed_title=str(r[1]) if r[1] is not None else None,
                    parsed_title_normalized=str(r[2]) if r[2] is not None else None,
                    parsed_year=int(r[3]) if r[3] is not None else None,
                    sidecar_group_key=str(sc) if sc is not None else None,
                    media_kind=str(r[5]),
                ),
            )
        return out

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupSyncBundle]) -> None:
        """루트 단위 전체 재구성.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            bundles: 새 그룹 묶음.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                cur_snap = self._conn.execute(
                    """
                    SELECT tg.group_key, gtm.tmdb_id, gtm.match_status, gtm.match_score
                    FROM group_tmdb_matches gtm
                    INNER JOIN title_groups tg ON tg.id = gtm.group_id
                    WHERE tg.root_id = ?
                    """,
                    (int(root_id),),
                )
                preserved = [
                    (
                        str(r[0]),
                        int(r[1]),
                        str(r[2]),
                        float(r[3]) if r[3] is not None else None,
                    )
                    for r in cur_snap.fetchall()
                ]
                self._conn.execute("DELETE FROM title_groups WHERE root_id = ?", (root_id,))
                for b in bundles:
                    n = len(b.members)
                    cur = self._conn.execute(
                        """
                        INSERT INTO title_groups (
                            root_id, group_key, group_type, group_confidence,
                            canonical_title, canonical_title_normalized,
                            tmdb_series_id, member_count, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            root_id,
                            b.group_key,
                            b.group_type,
                            b.group_confidence,
                            b.canonical_title,
                            b.canonical_title_normalized,
                            b.tmdb_series_id,
                            n,
                            now,
                            now,
                        ),
                    )
                    rid = cur.lastrowid
                    if rid is None:
                        msg = "INSERT title_groups did not yield row id"
                        raise RuntimeError(msg)
                    gid = int(rid)
                    self._conn.executemany(
                        """
                        INSERT INTO title_group_members (
                            group_id, media_file_id, member_role, score
                        ) VALUES (?, ?, ?, ?)
                        """,
                        [(gid, m.media_file_id, m.member_role, m.score) for m in b.members],
                    )
                ts_restore = utc_now_sqlite_text()
                for gkey, tmdb_id, match_status, match_score in preserved:
                    cur_gid = self._conn.execute(
                        """
                        SELECT id FROM title_groups
                        WHERE root_id = ? AND group_key = ?
                        LIMIT 1
                        """,
                        (int(root_id), gkey),
                    )
                    row_gid = cur_gid.fetchone()
                    if row_gid is None:
                        continue
                    new_gid = int(row_gid[0])
                    self._conn.execute(
                        GROUP_TMDB_MATCH_UPSERT_SQL,
                        (
                            new_gid,
                            tmdb_id,
                            match_status,
                            match_score,
                            ts_restore,
                            ts_restore,
                        ),
                    )
                    if match_status == "rejected":
                        self._conn.execute(
                            """
                            UPDATE title_groups
                            SET tmdb_series_id = NULL, updated_at = ?
                            WHERE id = ?
                            """,
                            (ts_restore, new_gid),
                        )
                    else:
                        self._conn.execute(
                            """
                            UPDATE title_groups
                            SET tmdb_series_id = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (tmdb_id, ts_restore, new_gid),
                        )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def replace_group_members(
        self,
        group_id: int,
        members: list[TitleGroupMemberSync],
    ) -> None:
        """한 그룹 멤버 전체 교체.

        Args:
            self: 저장소.
            group_id: 그룹 ID.
            members: 새 멤버.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                self._conn.execute(
                    "DELETE FROM title_group_members WHERE group_id = ?",
                    (group_id,),
                )
                self._conn.executemany(
                    """
                    INSERT INTO title_group_members (
                        group_id, media_file_id, member_role, score
                    ) VALUES (?, ?, ?, ?)
                    """,
                    [(group_id, m.media_file_id, m.member_role, m.score) for m in members],
                )
                self._conn.execute(
                    """
                    UPDATE title_groups SET member_count = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (len(members), now, group_id),
                )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
        """루트별 그룹 메타 조회.

        Args:
            self: 저장소.
            root_id: 루트 ID.

        Returns:
            목록.
        """
        sql = """
            SELECT id, root_id, group_key, group_type, member_count,
                   canonical_title, canonical_title_normalized
            FROM title_groups
            WHERE root_id = ?
            ORDER BY group_key
        """
        with self._lock:
            cur = self._conn.execute(sql, (root_id,))
            rows = cur.fetchall()
            self._conn.commit()
        out: list[TitleGroupListRecord] = []
        for r in rows:
            out.append(
                TitleGroupListRecord(
                    id=int(r[0]),
                    root_id=int(r[1]),
                    group_key=str(r[2]),
                    group_type=str(r[3]),
                    member_count=int(r[4]),
                    canonical_title=str(r[5]) if r[5] is not None else None,
                    canonical_title_normalized=str(r[6]) if r[6] is not None else None,
                ),
            )
        return out

    def get_group_id(self, root_id: int, group_key: str) -> int | None:
        """루트·group_key로 title_groups.id를 조회한다.

        Args:
            self: 저장소.
            root_id: 루트 id.
            group_key: 그룹 키 문자열.

        Returns:
            그룹 id. 없으면 None.
        """
        gk = (group_key or "").strip()
        if not gk:
            return None
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT id FROM title_groups
                WHERE root_id = ? AND group_key = ?
                LIMIT 1
                """,
                (int(root_id), gk),
            )
            row = cur.fetchone()
            self._conn.commit()
        return int(row[0]) if row is not None else None

    def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None:
        """path_norm에 해당하는 멤버가 속한 그룹 id를 반환한다.

        Args:
            self: 저장소.
            root_id: 루트 id.
            path_norm: 인덱스 `path_norm`.

        Returns:
            그룹 id. 없으면 None.
        """
        pn = (path_norm or "").strip()
        if not pn:
            return None
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT g.id
                FROM title_groups g
                INNER JOIN title_group_members m ON m.group_id = g.id
                INNER JOIN media_files f ON f.id = m.media_file_id
                WHERE g.root_id = ? AND f.path_norm = ?
                LIMIT 1
                """,
                (int(root_id), pn),
            )
            row = cur.fetchone()
            self._conn.commit()
        return int(row[0]) if row is not None else None
