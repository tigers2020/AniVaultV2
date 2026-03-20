"""Port: metadata search (TMDB 등). Use cases depend on this; adapters implement it."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO


@runtime_checkable
class MetadataProvider(Protocol):
    """메타데이터 공급자 계약. TMDB 어댑터가 구현."""

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        """제목(및 연도)으로 시리즈 후보 검색."""
        ...
