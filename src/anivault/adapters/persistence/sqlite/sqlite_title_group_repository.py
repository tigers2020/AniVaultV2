"""SQLite implementation of title group persistence."""

from __future__ import annotations

import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sql_queries import GROUP_TMDB_MATCH_UPSERT_SQL
from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.adapters.persistence.sqlite.sqlite_transaction import sqlite_transaction
from anivault.constants.adapters.sqlite import SQLITE_LOOKUP_CHUNK
from anivault.constants.application.statuses import (
    MATCH_STATUS_REJECTED,
    PARSE_CACHE_STATUS_OK,
)
from anivault.contracts.title_groups import (
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)


class SqliteTitleGroupRepository:
    """SQLite-backed title group repository."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        self._conn = conn
        self._lock = lock

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingRow]:
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
              AND c.parse_status = ?
            ORDER BY m.id
        """
        with self._lock:
            cur = self._conn.execute(sql, (root_id, PARSE_CACHE_STATUS_OK))
            rows = cur.fetchall()
            self._conn.commit()
        return [
            TitleGroupingRow(
                media_file_id=int(row[0]),
                parsed_title=str(row[1]) if row[1] is not None else None,
                parsed_title_normalized=str(row[2]) if row[2] is not None else None,
                parsed_year=int(row[3]) if row[3] is not None else None,
                sidecar_group_key=str(row[4]) if row[4] is not None else None,
                media_kind=str(row[5]),
            )
            for row in rows
        ]

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupBundle]) -> None:
        now = utc_now_sqlite_text()
        with self._lock, sqlite_transaction(self._conn):
            existing_matches: dict[str, tuple[int, str, float | None]] = {}
            cur = self._conn.execute(
                """
                    SELECT g.group_key, m.tmdb_id, m.match_status, m.match_score
                    FROM title_groups g
                    INNER JOIN group_tmdb_matches m ON m.group_id = g.id
                    WHERE g.root_id = ?
                    """,
                (root_id,),
            )
            for row in cur.fetchall():
                existing_matches[str(row[0])] = (
                    int(row[1]),
                    str(row[2]),
                    float(row[3]) if row[3] is not None else None,
                )
            self._conn.execute("DELETE FROM title_groups WHERE root_id = ?", (root_id,))
            for bundle in bundles:
                preserved = existing_matches.get(bundle.group_key)
                tmdb_series_id = preserved[0] if preserved is not None else bundle.tmdb_series_id
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
                        bundle.group_key,
                        bundle.group_type,
                        bundle.group_confidence,
                        bundle.canonical_title,
                        bundle.canonical_title_normalized,
                        tmdb_series_id,
                        len(bundle.members),
                        now,
                        now,
                    ),
                )
                row_id = cur.lastrowid
                if row_id is None:
                    raise RuntimeError("INSERT title_groups did not yield row id")
                group_id = int(row_id)
                if preserved is not None:
                    self._conn.execute(
                        GROUP_TMDB_MATCH_UPSERT_SQL,
                        (group_id, preserved[0], preserved[1], preserved[2], now, now),
                    )
                    tmdb_series_id = None if preserved[1] == MATCH_STATUS_REJECTED else preserved[0]
                    self._conn.execute(
                        """
                            UPDATE title_groups
                            SET tmdb_series_id = ?, updated_at = ?
                            WHERE id = ?
                            """,
                        (tmdb_series_id, now, group_id),
                    )
                self._conn.executemany(
                    """
                        INSERT INTO title_group_members (
                            group_id, media_file_id, member_role, score
                        ) VALUES (?, ?, ?, ?)
                        """,
                    [
                        (group_id, member.media_file_id, member.member_role, member.score)
                        for member in bundle.members
                    ],
                )

    def replace_group_members(self, group_id: int, members: list[TitleGroupMember]) -> None:
        now = utc_now_sqlite_text()
        with self._lock, sqlite_transaction(self._conn):
            self._conn.execute("DELETE FROM title_group_members WHERE group_id = ?", (group_id,))
            self._conn.executemany(
                """
                    INSERT INTO title_group_members (
                        group_id, media_file_id, member_role, score
                    ) VALUES (?, ?, ?, ?)
                    """,
                [
                    (group_id, member.media_file_id, member.member_role, member.score)
                    for member in members
                ],
            )
            self._conn.execute(
                """
                    UPDATE title_groups SET member_count = ?, updated_at = ?
                    WHERE id = ?
                    """,
                (len(members), now, group_id),
            )

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
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
        return [
            TitleGroupListRecord(
                id=int(row[0]),
                root_id=int(row[1]),
                group_key=str(row[2]),
                group_type=str(row[3]),
                member_count=int(row[4]),
                canonical_title=str(row[5]) if row[5] is not None else None,
                canonical_title_normalized=str(row[6]) if row[6] is not None else None,
            )
            for row in rows
        ]

    def get_group_id(self, root_id: int, group_key: str) -> int | None:
        cleaned = (group_key or "").strip()
        if not cleaned:
            return None
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT id FROM title_groups
                WHERE root_id = ? AND group_key = ?
                LIMIT 1
                """,
                (int(root_id), cleaned),
            )
            row = cur.fetchone()
            self._conn.commit()
        return int(row[0]) if row is not None else None

    def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None:
        matches = self.get_group_ids_for_path_norms(root_id, [path_norm])
        return matches.get((path_norm or "").strip())

    def get_group_ids_for_path_norms(
        self,
        root_id: int,
        path_norms: list[str],
    ) -> dict[str, int]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for path_norm in path_norms:
            normalized = (path_norm or "").strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                cleaned.append(normalized)
        if not cleaned:
            return {}
        matches: dict[str, int] = {}
        with self._lock:
            for start in range(0, len(cleaned), SQLITE_LOOKUP_CHUNK):
                chunk = cleaned[start : start + SQLITE_LOOKUP_CHUNK]
                placeholders = ",".join("?" for _ in chunk)
                cur = self._conn.execute(
                    f"""
                    SELECT f.path_norm, g.id
                    FROM media_files f
                    INNER JOIN title_group_members m ON m.media_file_id = f.id
                    INNER JOIN title_groups g ON g.id = m.group_id
                    WHERE g.root_id = ?
                      AND f.path_norm IN ({placeholders})
                    """,
                    (int(root_id), *chunk),
                )
                for row in cur.fetchall():
                    path_norm = str(row[0])
                    if path_norm not in matches:
                        matches[path_norm] = int(row[1])
        return matches
