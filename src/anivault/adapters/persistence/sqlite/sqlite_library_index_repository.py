"""sqlite_library_index_repository.py

`LibraryIndexRepository` SQLite 구현. 연결 공유 시 외부에서 동일 Lock 사용.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.library_index import IndexedMediaForParse, MediaFileRecord
from anivault.application.ports.library_index_port import ScanSessionStatus
from anivault.domain.path_norm import (
    dir_norm_for_relative,
    infer_dest_library_root,
    normalize_path_key,
    relative_posix_under_root,
)
from anivault.domain.services.sidecar_group_key import compute_sidecar_group_key

_MARK_MISSING_INLINE_LIMIT = 500


class SqliteLibraryIndexRepository:
    """라이브러리 인덱스 SQLite 저장소."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 스레드 직렬화용 Lock을 받는다.

        Args:
            self: 저장소.
            conn: 공유 SQLite 연결(`check_same_thread=False` 전제).
            lock: 메서드 단위 직렬화용 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def upsert_root(self, root_path: str, *, display_name: str | None = None) -> int:
        """루트 행을 upsert하고 ID를 반환한다.

        Args:
            self: 저장소.
            root_path: 스캔 루트.
            display_name: 표시명.

        Returns:
            `library_roots.id`.
        """
        with self._lock:
            return self._upsert_root_path_locked(root_path, display_name=display_name)

    def _upsert_root_path_locked(self, root_path: str, *, display_name: str | None = None) -> int:
        """`self._lock`을 잡은 상태에서 루트 행을 upsert한다.

        Args:
            self: 저장소.
            root_path: 스캔 루트.
            display_name: 표시명.

        Returns:
            `library_roots.id`.
        """
        pnorm = normalize_path_key(root_path)
        disp = display_name if display_name is not None else None
        now = utc_now_sqlite_text()
        cur = self._conn.execute(
            """
            INSERT INTO library_roots (
                root_path, path_norm, display_name, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, 1, ?, ?)
            ON CONFLICT(path_norm) DO UPDATE SET
                root_path = excluded.root_path,
                display_name = COALESCE(excluded.display_name, library_roots.display_name),
                updated_at = excluded.updated_at
            RETURNING id
            """,
            (pnorm, pnorm, disp, now, now),
        )
        row = cur.fetchone()
        self._conn.commit()
        assert row is not None
        return int(row[0])

    def _longest_library_root_covering_locked(self, file_resolved: Path) -> tuple[int, str] | None:
        """파일이 그 아래에 있도록 등록된 루트 중 `path_norm`이 가장 긴 행을 고른다.

        Args:
            self: 저장소.
            file_resolved: 해결된 절대 파일 경로.

        Returns:
            `(id, root_path)` 또는 없으면 None.
        """
        cur = self._conn.execute("SELECT id, root_path FROM library_roots")
        best: tuple[int, str] | None = None
        best_len = -1
        for rid, rpath in cur.fetchall():
            rp = Path(str(rpath)).expanduser()
            try:
                file_resolved.relative_to(rp.resolve())
            except ValueError:
                continue
            ln = len(str(rpath))
            if ln > best_len:
                best_len = ln
                best = (int(rid), str(rpath))
        return best

    def begin_scan(self, root_id: int, scan_kind: str) -> int:
        """`running` 세션을 추가한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            scan_kind: 스캔 종류.

        Returns:
            세션 ID.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO scan_sessions (
                    root_id, scan_kind, started_at, status,
                    files_seen, files_added, files_updated, files_removed
                ) VALUES (?, ?, ?, 'running', 0, 0, 0, 0)
                RETURNING id
                """,
                (root_id, scan_kind, now),
            )
            row = cur.fetchone()
            self._conn.commit()
        assert row is not None
        return int(row[0])

    def finish_scan(
        self,
        session_id: int,
        *,
        status: ScanSessionStatus,
        files_seen: int,
        files_added: int,
        files_updated: int,
        files_removed: int,
        error_message: str | None = None,
    ) -> None:
        """세션 종료 필드를 기록하고, 성공 시 루트 `last_scan_at`을 갱신한다.

        Args:
            self: 저장소.
            session_id: 세션 ID.
            status: 종료 상태.
            files_seen: 본 파일 수.
            files_added: 추가 수.
            files_updated: 갱신 수.
            files_removed: 제거(soft) 수.
            error_message: 오류 메시지.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                "SELECT root_id FROM scan_sessions WHERE id = ?",
                (session_id,),
            )
            root_row = cur.fetchone()
            if root_row is None:
                self._conn.commit()
                return
            root_id = int(root_row[0])
            self._conn.execute(
                """
                UPDATE scan_sessions SET
                    finished_at = ?,
                    status = ?,
                    files_seen = ?,
                    files_added = ?,
                    files_updated = ?,
                    files_removed = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (
                    now,
                    status,
                    files_seen,
                    files_added,
                    files_updated,
                    files_removed,
                    error_message,
                    session_id,
                ),
            )
            if status == "success":
                self._conn.execute(
                    "UPDATE library_roots SET last_scan_at = ?, updated_at = ? WHERE id = ?",
                    (now, now, root_id),
                )
            self._conn.commit()

    def upsert_media_file(
        self,
        root_id: int,
        session_id: int,
        *,
        absolute_path: str,
        media_kind: str,
    ) -> tuple[bool, bool]:
        """미디어 파일 메타 upsert.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            session_id: 스캔 세션 ID.
            absolute_path: 절대 경로.
            media_kind: 분류 문자열.

        Returns:
            `(is_new, is_updated)`.
        """
        path = Path(absolute_path)
        file_name = path.name
        file_stem = path.stem
        extension = path.suffix.lower() if path.suffix else ""
        st = path.stat()
        size_bytes = int(st.st_size)
        mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
        ctime_ns: int | None = int(st.st_ctime_ns) if hasattr(st, "st_ctime_ns") else None
        inode_hint = str(st.st_ino) if hasattr(st, "st_ino") else None
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                "SELECT root_path FROM library_roots WHERE id = ?",
                (root_id,),
            )
            rr = cur.fetchone()
            if rr is None:
                self._conn.commit()
                raise ValueError(f"unknown root_id: {root_id}")
            root_display = str(rr[0])
            rel = relative_posix_under_root(root_display, absolute_path)
            pnorm = normalize_path_key(absolute_path)
            dnorm = dir_norm_for_relative(rel)
            sidecar_key = compute_sidecar_group_key(
                media_kind=media_kind,
                dir_norm=dnorm,
                file_stem=file_stem,
            )
            cur = self._conn.execute(
                "SELECT id FROM media_files WHERE root_id = ? AND path_norm = ?",
                (root_id, pnorm),
            )
            existed = cur.fetchone() is not None
            if existed:
                self._conn.execute(
                    """
                    UPDATE media_files SET
                        relative_path = ?,
                        dir_norm = ?,
                        file_name = ?,
                        file_stem = ?,
                        extension = ?,
                        media_kind = ?,
                        size_bytes = ?,
                        mtime_ns = ?,
                        ctime_ns = ?,
                        inode_hint = ?,
                        sidecar_group_key = ?,
                        is_deleted = 0,
                        first_seen_scan_id = COALESCE(first_seen_scan_id, ?),
                        last_seen_scan_id = ?,
                        updated_at = ?
                    WHERE root_id = ? AND path_norm = ?
                    """,
                    (
                        rel,
                        dnorm,
                        file_name,
                        file_stem,
                        extension,
                        media_kind,
                        size_bytes,
                        mtime_ns,
                        ctime_ns,
                        inode_hint,
                        sidecar_key,
                        session_id,
                        session_id,
                        now,
                        root_id,
                        pnorm,
                    ),
                )
                self._conn.commit()
                return (False, True)
            self._conn.execute(
                """
                INSERT INTO media_files (
                    root_id, relative_path, path_norm, dir_norm,
                    file_name, file_stem, extension, media_kind,
                    size_bytes, mtime_ns, ctime_ns, inode_hint,
                    content_fingerprint, sidecar_group_key,
                    is_deleted, first_seen_scan_id, last_seen_scan_id,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    NULL, ?,
                    0, ?, ?,
                    ?, ?
                )
                """,
                (
                    root_id,
                    rel,
                    pnorm,
                    dnorm,
                    file_name,
                    file_stem,
                    extension,
                    media_kind,
                    size_bytes,
                    mtime_ns,
                    ctime_ns,
                    inode_hint,
                    sidecar_key,
                    session_id,
                    session_id,
                    now,
                    now,
                ),
            )
            self._conn.commit()
            return (True, False)

    def mark_missing_deleted(self, root_id: int, session_id: int, seen_path_norms: set[str]) -> int:
        """스캔에 없는 기존 행을 soft-delete한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            session_id: 세션 ID.
            seen_path_norms: 본 경로 키 집합.

        Returns:
            갱신된 행 수.
        """
        del session_id
        now = utc_now_sqlite_text()
        with self._lock:
            if not seen_path_norms:
                cur = self._conn.execute(
                    """
                    UPDATE media_files
                    SET is_deleted = 1, updated_at = ?
                    WHERE root_id = ? AND is_deleted = 0
                    """,
                    (now, root_id),
                )
                n = cur.rowcount if cur.rowcount is not None else 0
                self._conn.commit()
                return int(n)
            if len(seen_path_norms) <= _MARK_MISSING_INLINE_LIMIT:
                placeholders = ",".join("?" * len(seen_path_norms))
                params: list[object] = [now, root_id, *seen_path_norms]
                cur = self._conn.execute(
                    f"""
                    UPDATE media_files
                    SET is_deleted = 1, updated_at = ?
                    WHERE root_id = ? AND is_deleted = 0
                      AND path_norm NOT IN ({placeholders})
                    """,
                    params,
                )
                n = cur.rowcount if cur.rowcount is not None else 0
                self._conn.commit()
                return int(n)
            self._conn.execute("""
                CREATE TEMP TABLE IF NOT EXISTS _anivault_seen_path_norm (
                    path_norm TEXT PRIMARY KEY
                )
                """)
            self._conn.execute("DELETE FROM _anivault_seen_path_norm")
            self._conn.executemany(
                "INSERT INTO _anivault_seen_path_norm (path_norm) VALUES (?)",
                [(p,) for p in seen_path_norms],
            )
            cur = self._conn.execute(
                """
                UPDATE media_files
                SET is_deleted = 1, updated_at = ?
                WHERE root_id = ? AND is_deleted = 0
                  AND path_norm NOT IN (SELECT path_norm FROM _anivault_seen_path_norm)
                """,
                (now, root_id),
            )
            n = cur.rowcount if cur.rowcount is not None else 0
            self._conn.commit()
            return int(n)

    def resolve_media_for_parse(
        self,
        root_id: int,
        absolute_paths: list[str],
    ) -> list[IndexedMediaForParse | None]:
        """절대 경로 순서를 유지하며 인덱스 메타를 조회한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            absolute_paths: 절대 경로 목록(중복 허용).

        Returns:
            입력과 동일 길이. 매칭 실패·삭제 행은 None.
        """
        if not absolute_paths:
            return []
        keys_in_order = [normalize_path_key(p) for p in absolute_paths]
        unique_keys: list[str] = []
        seen_u: set[str] = set()
        for k in keys_in_order:
            if k not in seen_u:
                seen_u.add(k)
                unique_keys.append(k)
        placeholders = ",".join("?" * len(unique_keys))
        sql = f"""
            SELECT path_norm, id, size_bytes, mtime_ns
            FROM media_files
            WHERE root_id = ? AND is_deleted = 0 AND path_norm IN ({placeholders})
        """
        params: list[object] = [root_id, *unique_keys]
        with self._lock:
            cur = self._conn.execute(sql, params)
            rows = cur.fetchall()
            self._conn.commit()
        by_norm: dict[str, IndexedMediaForParse] = {}
        for r in rows:
            pn = str(r[0])
            by_norm[pn] = IndexedMediaForParse(
                id=int(r[1]),
                path_norm=pn,
                size_bytes=int(r[2]),
                mtime_ns=int(r[3]),
            )
        return [by_norm.get(k) for k in keys_in_order]

    def list_media_by_root(
        self,
        root_id: int,
        *,
        include_deleted: bool = False,
    ) -> list[MediaFileRecord]:
        """루트별 미디어 목록.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            include_deleted: 삭제 표시 포함 여부.

        Returns:
            레코드 목록.
        """
        with self._lock:
            if include_deleted:
                cur = self._conn.execute(
                    """
                    SELECT id, root_id, relative_path, path_norm, media_kind, is_deleted
                    FROM media_files
                    WHERE root_id = ?
                    ORDER BY path_norm
                    """,
                    (root_id,),
                )
            else:
                cur = self._conn.execute(
                    """
                    SELECT id, root_id, relative_path, path_norm, media_kind, is_deleted
                    FROM media_files
                    WHERE root_id = ? AND is_deleted = 0
                    ORDER BY path_norm
                    """,
                    (root_id,),
                )
            rows = cur.fetchall()
            self._conn.commit()
        out: list[MediaFileRecord] = []
        for r in rows:
            out.append(
                MediaFileRecord(
                    id=int(r[0]),
                    root_id=int(r[1]),
                    relative_path=str(r[2]),
                    path_norm=str(r[3]),
                    media_kind=str(r[4]),
                    is_deleted=bool(r[5]),
                )
            )
        return out

    def relocate_media_file(
        self,
        root_id: int,
        *,
        old_absolute_path: str,
        new_absolute_path: str,
    ) -> bool:
        """이동 후 절대 경로로 경로·크기·mtime 등을 갱신한다. 행 id·media_kind·지문은 유지.

        새 경로가 원래 `root_id` 루트 밖이면(정리 출력 폴더 등) 등록된 더 넓은 루트를 고르거나
        루트를 추론해 upsert한 뒤 `root_id`를 바꾼다. 루트가 바뀌면 해당 파일의
        `title_group_members` 행은 제거된다(이후 동기화로 재구성).

        물리 이동이 목적지를 덮어쓴 뒤 호출되는 것이 전제이므로, 목적지 `path_norm`에 남아 있던
        다른 인덱스 행(스테일)이 있으면 `parse_cache`·`media_files`에서 제거한 뒤 갱신한다.

        Args:
            self: 저장소.
            root_id: 이동 전 미디어가 속했던 루트 ID.
            old_absolute_path: 이동 전 절대 경로.
            new_absolute_path: 이동 후 절대 경로.

        Returns:
            갱신 성공이면 True, 해당 `path_norm` 행이 없으면 False.
        """
        old_pnorm = normalize_path_key(old_absolute_path)
        path = Path(new_absolute_path)
        now = utc_now_sqlite_text()
        with self._lock:
            cur = self._conn.execute(
                "SELECT root_path FROM library_roots WHERE id = ?",
                (root_id,),
            )
            rr = cur.fetchone()
            if rr is None:
                self._conn.commit()
                return False
            root_display = str(rr[0])
            cur = self._conn.execute(
                """
                SELECT id, media_kind FROM media_files
                WHERE root_id = ? AND path_norm = ? AND is_deleted = 0
                """,
                (root_id, old_pnorm),
            )
            kind_row = cur.fetchone()
            if kind_row is None:
                self._conn.commit()
                return False
            media_id = int(kind_row[0])
            media_kind = str(kind_row[1])
            file_name = path.name
            file_stem = path.stem
            extension = path.suffix.lower() if path.suffix else ""
            st = path.stat()
            size_bytes = int(st.st_size)
            mtime_ns = int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)))
            ctime_ns: int | None = int(st.st_ctime_ns) if hasattr(st, "st_ctime_ns") else None
            inode_hint = str(st.st_ino) if hasattr(st, "st_ino") else None
            new_resolved = path.expanduser().resolve()
            try:
                rel = relative_posix_under_root(root_display, new_absolute_path)
                target_root_id = root_id
                target_root_display = root_display
            except ValueError:
                hit = self._longest_library_root_covering_locked(new_resolved)
                if hit is not None:
                    target_root_id, target_root_display = hit
                else:
                    inferred = infer_dest_library_root(
                        Path(root_display).expanduser().resolve(),
                        new_resolved,
                    )
                    target_root_id = self._upsert_root_path_locked(str(inferred))
                    target_root_display = normalize_path_key(str(inferred))
                rel = relative_posix_under_root(target_root_display, new_absolute_path)
            new_pnorm = normalize_path_key(new_absolute_path)
            dnorm = dir_norm_for_relative(rel)
            sidecar_key = compute_sidecar_group_key(
                media_kind=media_kind,
                dir_norm=dnorm,
                file_stem=file_stem,
            )
            cur = self._conn.execute(
                """
                SELECT id FROM media_files
                WHERE root_id = ? AND path_norm = ? AND id != ?
                """,
                (target_root_id, new_pnorm, media_id),
            )
            occ = cur.fetchone()
            if occ is not None:
                stale_id = int(occ[0])
                self._conn.execute(
                    "DELETE FROM parse_cache WHERE media_file_id = ?",
                    (stale_id,),
                )
                self._conn.execute(
                    "DELETE FROM media_files WHERE id = ?",
                    (stale_id,),
                )
            if target_root_id != root_id:
                self._conn.execute(
                    "DELETE FROM title_group_members WHERE media_file_id = ?",
                    (media_id,),
                )
            cur = self._conn.execute(
                """
                UPDATE media_files SET
                    root_id = ?,
                    relative_path = ?,
                    path_norm = ?,
                    dir_norm = ?,
                    file_name = ?,
                    file_stem = ?,
                    extension = ?,
                    size_bytes = ?,
                    mtime_ns = ?,
                    ctime_ns = ?,
                    inode_hint = ?,
                    sidecar_group_key = ?,
                    updated_at = ?
                WHERE root_id = ? AND path_norm = ?
                """,
                (
                    target_root_id,
                    rel,
                    new_pnorm,
                    dnorm,
                    file_name,
                    file_stem,
                    extension,
                    size_bytes,
                    mtime_ns,
                    ctime_ns,
                    inode_hint,
                    sidecar_key,
                    now,
                    root_id,
                    old_pnorm,
                ),
            )
            n = cur.rowcount if cur.rowcount is not None else 0
            self._conn.commit()
        return n > 0

    def relocate_media_files(
        self,
        root_id: int,
        *,
        pairs: tuple[tuple[str, str], ...],
    ) -> None:
        """`relocate_media_file`를 순서대로 적용한다.

        Args:
            self: 저장소.
            root_id: 루트 ID.
            pairs: `(이동 전, 이동 후)` 절대 경로 쌍.

        Returns:
            None.
        """
        for old_p, new_p in pairs:
            self.relocate_media_file(
                root_id,
                old_absolute_path=old_p,
                new_absolute_path=new_p,
            )
