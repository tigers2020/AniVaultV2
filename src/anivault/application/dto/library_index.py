"""library_index.py

라이브러리 인덱스 조회용 경량 DTO.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BulkMediaUpsertItem:
    """Input row for bulk media index upsert."""

    absolute_path: str
    media_kind: str


@dataclass(frozen=True)
class BulkMediaUpsertResult:
    """Summary from bulk media index upsert."""

    files_added: int
    files_updated: int
    seen_path_norms: set[str]


@dataclass(frozen=True)
class MediaFileRecord:
    """media_files 행 요약."""

    id: int
    root_id: int
    relative_path: str
    path_norm: str
    media_kind: str
    is_deleted: bool


@dataclass(frozen=True)
class IndexedMediaForParse:
    """파싱 캐시용: 경로에 대응하는 인덱스 행 메타."""

    id: int
    path_norm: str
    size_bytes: int
    mtime_ns: int
