"""Port: metadata search (TMDB 등). Use cases depend on this; adapters implement it."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class MetadataProvider(Protocol):
    """메타데이터 공급자 계약. TMDB 어댑터가 구현."""

    def search_series(self, query: str, *, year: int | None = None) -> list[object]:
        """제목(및 연도)으로 시리즈 후보 검색. 구체 타입은 DTO로 정의."""
        ...
