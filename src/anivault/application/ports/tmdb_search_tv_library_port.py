"""Port for cached TMDB search TV library rows."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.contracts.tmdb import SearchTvLibraryRecord


@runtime_checkable
class TmdbSearchTvLibraryRepository(Protocol):
    def upsert(self, record: SearchTvLibraryRecord) -> None: ...

    def get(self, tmdb_id: int, language: str) -> SearchTvLibraryRecord | None: ...
