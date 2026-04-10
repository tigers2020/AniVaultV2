"""Library index contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BulkMediaUpsertItem:
    """Input row for bulk media index upsert."""

    absolute_path: str
    media_kind: str


@dataclass(frozen=True, slots=True)
class BulkMediaUpsertResult:
    """Summary from bulk media index upsert."""

    files_added: int
    files_updated: int
    seen_path_norms: set[str]


@dataclass(frozen=True, slots=True)
class MediaFileRecord:
    """Read model for indexed media files."""

    id: int
    root_id: int
    relative_path: str
    path_norm: str
    media_kind: str
    is_deleted: bool


@dataclass(frozen=True, slots=True)
class IndexedMediaForParse:
    """Indexed media metadata needed to resolve parse cache entries."""

    id: int
    path_norm: str
    size_bytes: int
    mtime_ns: int
