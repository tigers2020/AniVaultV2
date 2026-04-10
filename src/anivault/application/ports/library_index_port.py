"""Port for library index persistence."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Literal, Protocol, runtime_checkable

from anivault.contracts.library_index import (
    BulkMediaUpsertItem,
    BulkMediaUpsertResult,
    IndexedMediaForParse,
    MediaFileRecord,
)

ScanSessionStatus = Literal["success", "failed", "cancelled"]


@runtime_checkable
class LibraryIndexRepository(Protocol):
    def upsert_root(self, root_path: str, *, display_name: str | None = None) -> int: ...

    def begin_scan(self, root_id: int, scan_kind: str) -> int: ...

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
    ) -> None: ...

    def upsert_media_file(
        self,
        root_id: int,
        session_id: int,
        *,
        absolute_path: str,
        media_kind: str,
    ) -> tuple[bool, bool]: ...

    def upsert_media_files(
        self,
        root_id: int,
        session_id: int,
        files: list[BulkMediaUpsertItem],
    ) -> BulkMediaUpsertResult: ...

    def media_upsert_batch(self) -> AbstractContextManager[None]: ...

    def mark_missing_deleted(
        self, root_id: int, session_id: int, seen_path_norms: set[str]
    ) -> int: ...

    def resolve_media_for_parse(
        self,
        root_id: int,
        absolute_paths: list[str],
    ) -> list[IndexedMediaForParse | None]: ...

    def list_media_by_root(
        self,
        root_id: int,
        *,
        include_deleted: bool = False,
    ) -> list[MediaFileRecord]: ...

    def relocate_media_file(
        self,
        root_id: int,
        *,
        old_absolute_path: str,
        new_absolute_path: str,
    ) -> bool: ...

    def relocate_media_files(
        self,
        root_id: int,
        *,
        pairs: tuple[tuple[str, str], ...],
    ) -> None: ...
