"""sqlite_library_index_repository.py

`LibraryIndexRepository` SQLite 구현. 연결 공유 시 외부에서 동일 Lock 사용.

Author: Pom Kim
"""

from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.library_index import (
    BulkMediaUpsertItem,
    BulkMediaUpsertResult,
    IndexedMediaForParse,
    MediaFileRecord,
)
from anivault.application.ports.library_index_port import ScanSessionStatus
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.services.sidecar_group_key import compute_sidecar_group_key

_MARK_MISSING_INLINE_LIMIT = 500
_EXISTING_LOOKUP_CHUNK = 500


@dataclass(frozen=True)
class _MediaFileUpsertRow:
    relative_path: str
    path_norm: str
    dir_norm: str
    file_name: str
    file_stem: str
    extension: str
    media_kind: str
    size_bytes: int
    mtime_ns: int
    ctime_ns: int | None
    inode_hint: str | None
    sidecar_group_key: str | None


@dataclass(frozen=True)
class _ResolvedRootPath:
    root_text: str
    root_posix: str
    root_cmp: str
    root_cmp_prefix: str


def _path_key_from_posix(path_posix: str) -> str:
    """Normalize a POSIX path string that is already anchored to the library root."""
    s = path_posix
    if len(s) > 1 and s.endswith("/"):
        s = s.rstrip("/")
        if s.endswith(":"):
            s = s + "/"
    if os.name == "nt" or sys.platform.startswith("win"):
        return os.path.normcase(s)
    return s


def _path_key_from_known_path(path: Path) -> str:
    """Normalize a path that is already anchored to the resolved library root."""
    return _path_key_from_posix(path.as_posix())


def _resolved_root_path(root: str | Path) -> _ResolvedRootPath:
    root_resolved = Path(root).expanduser().resolve()
    root_text = os.path.normpath(os.fspath(root_resolved))
    root_cmp = os.path.normcase(root_text)
    return _ResolvedRootPath(
        root_text=root_text,
        root_posix=root_resolved.as_posix().rstrip("/"),
        root_cmp=root_cmp,
        root_cmp_prefix=root_cmp.rstrip("\\/") + os.sep,
    )


def _relative_posix_under_resolved_root(
    root: _ResolvedRootPath,
    absolute_path: str | PathLike[str],
) -> tuple[str, str]:
    """Return relative POSIX path and normalized key without resolving each file."""
    path_text = os.path.abspath(os.path.expanduser(os.fspath(absolute_path)))
    path_cmp = os.path.normcase(os.path.normpath(path_text))
    if not path_cmp.startswith(root.root_cmp_prefix):
        raise ValueError(f"path not under root: {path_text} vs {root.root_text}")
    rel_text = path_text[len(root.root_text.rstrip("\\/")) + 1 :]
    rel_posix = rel_text.replace("\\", "/")
    return rel_posix, _path_key_from_posix(f"{root.root_posix}/{rel_posix}")


def _dir_norm_for_relative_text(relative_posix: str) -> str:
    parent, sep, _name = relative_posix.rpartition("/")
    return parent if sep else ""


def _split_file_name_parts(relative_posix: str) -> tuple[str, str, str]:
    file_name = relative_posix.rsplit("/", 1)[-1]
    if file_name in {"", ".", ".."}:
        return file_name, file_name, ""
    stem, dot, suffix = file_name.rpartition(".")
    if dot and stem:
        return file_name, stem, f".{suffix}".lower()
    return file_name, file_name, ""


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
        pnorm = normalize_path_key(root_path)
        disp = display_name if display_name is not None else None
        now = utc_now_sqlite_text()
        with self._lock:
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
        result = self.upsert_media_files(
            root_id,
            session_id,
            [BulkMediaUpsertItem(absolute_path=absolute_path, media_kind=media_kind)],
        )
        return (result.files_added == 1, result.files_updated == 1)

    @contextmanager
    def media_upsert_batch(self) -> Iterator[None]:
        """Provide protocol compatibility for repositories that support per-file batching."""
        yield

    def _fetch_root_path(self, root_id: int) -> str:
        cur = self._conn.execute(
            "SELECT root_path FROM library_roots WHERE id = ?",
            (root_id,),
        )
        rr = cur.fetchone()
        if rr is None:
            raise ValueError(f"unknown root_id: {root_id}")
        return str(rr[0])

    def _media_file_upsert_row(
        self,
        item: BulkMediaUpsertItem,
        *,
        root: _ResolvedRootPath,
    ) -> _MediaFileUpsertRow:
        st = os.stat(item.absolute_path)
        rel, pnorm = _relative_posix_under_resolved_root(root, item.absolute_path)
        dnorm = _dir_norm_for_relative_text(rel)
        file_name, file_stem, extension = _split_file_name_parts(rel)
        return _MediaFileUpsertRow(
            relative_path=rel,
            path_norm=pnorm,
            dir_norm=dnorm,
            file_name=file_name,
            file_stem=file_stem,
            extension=extension,
            media_kind=item.media_kind,
            size_bytes=int(st.st_size),
            mtime_ns=int(getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))),
            ctime_ns=int(st.st_ctime_ns) if hasattr(st, "st_ctime_ns") else None,
            inode_hint=str(st.st_ino) if hasattr(st, "st_ino") else None,
            sidecar_group_key=compute_sidecar_group_key(
                media_kind=item.media_kind,
                dir_norm=dnorm,
                file_stem=file_stem,
            ),
        )

    def _fetch_existing_media_path_norms(
        self,
        root_id: int,
        path_norms: list[str],
    ) -> set[str]:
        existing: set[str] = set()
        for start in range(0, len(path_norms), _EXISTING_LOOKUP_CHUNK):
            chunk = path_norms[start : start + _EXISTING_LOOKUP_CHUNK]
            if not chunk:
                continue
            placeholders = ",".join("?" * len(chunk))
            cur = self._conn.execute(
                f"""
                SELECT path_norm FROM media_files
                WHERE root_id = ? AND path_norm IN ({placeholders})
                """,
                (root_id, *chunk),
            )
            existing.update(str(row[0]) for row in cur.fetchall())
        return existing

    def upsert_media_files(
        self,
        root_id: int,
        session_id: int,
        files: list[BulkMediaUpsertItem],
    ) -> BulkMediaUpsertResult:
        """Bulk media_files upsert for scan indexing."""
        if not files:
            return BulkMediaUpsertResult(
                files_added=0,
                files_updated=0,
                seen_path_norms=set(),
            )
        with self._lock:
            root_display = self._fetch_root_path(root_id)
            root = _resolved_root_path(root_display)
            rows_by_norm: dict[str, _MediaFileUpsertRow] = {}
            for item in files:
                row = self._media_file_upsert_row(item, root=root)
                rows_by_norm[row.path_norm] = row
            rows = list(rows_by_norm.values())
            seen_path_norms = set(rows_by_norm)
            existing = self._fetch_existing_media_path_norms(root_id, list(rows_by_norm))
            now = utc_now_sqlite_text()
            update_params = [
                (
                    row.relative_path,
                    row.dir_norm,
                    row.file_name,
                    row.file_stem,
                    row.extension,
                    row.media_kind,
                    row.size_bytes,
                    row.mtime_ns,
                    row.ctime_ns,
                    row.inode_hint,
                    row.sidecar_group_key,
                    session_id,
                    session_id,
                    now,
                    root_id,
                    row.path_norm,
                )
                for row in rows
                if row.path_norm in existing
            ]
            insert_params = [
                (
                    root_id,
                    row.relative_path,
                    row.path_norm,
                    row.dir_norm,
                    row.file_name,
                    row.file_stem,
                    row.extension,
                    row.media_kind,
                    row.size_bytes,
                    row.mtime_ns,
                    row.ctime_ns,
                    row.inode_hint,
                    row.sidecar_group_key,
                    session_id,
                    session_id,
                    now,
                    now,
                )
                for row in rows
                if row.path_norm not in existing
            ]
            self._conn.execute("BEGIN")
            try:
                if update_params:
                    self._conn.executemany(
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
                        update_params,
                    )
                if insert_params:
                    self._conn.executemany(
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
                        insert_params,
                    )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        return BulkMediaUpsertResult(
            files_added=len(insert_params),
            files_updated=len(update_params),
            seen_path_norms=seen_path_norms,
        )

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
        with self._lock:
            root_display = self._fetch_root_path(root_id)
        root = _resolved_root_path(root_display)
        keys_in_order: list[str | None] = []
        unique_keys: list[str] = []
        seen_u: set[str] = set()
        for path in absolute_paths:
            try:
                _rel, key = _relative_posix_under_resolved_root(root, path)
            except ValueError:
                keys_in_order.append(None)
                continue
            keys_in_order.append(key)
            if key not in seen_u:
                seen_u.add(key)
                unique_keys.append(key)
        if not unique_keys:
            return [None for _ in keys_in_order]
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
        by_norm: dict[str, IndexedMediaForParse] = {}
        for r in rows:
            pn = str(r[0])
            by_norm[pn] = IndexedMediaForParse(
                id=int(r[1]),
                path_norm=pn,
                size_bytes=int(r[2]),
                mtime_ns=int(r[3]),
            )
        return [by_norm.get(k) if k is not None else None for k in keys_in_order]

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
