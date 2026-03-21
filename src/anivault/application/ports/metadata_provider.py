"""metadata_provider.py

메타데이터 검색 포트(TMDB 등). 유스케이스는 이 Protocol에만 의존하고 어댑터가 구현한다.

Author: Pom Kim
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO


@runtime_checkable
class MetadataProvider(Protocol):
    """메타데이터 공급자 계약. TMDB 어댑터가 구현."""

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        """제목(및 연도)으로 시리즈 후보를 검색한다.

        Args:
            self: 메타데이터 공급자 인스턴스.
            query: 검색어(시리즈 제목).
            year: 방영 연도 필터. None이면 연도를 무시한다.

        Returns:
            시리즈 후보 DTO 시퀀스.
        """
        ...
