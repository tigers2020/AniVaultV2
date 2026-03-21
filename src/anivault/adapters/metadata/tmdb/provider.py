"""provider.py

tmdbapis 기반 MetadataProvider 구현.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Sequence

from anivault.adapters.metadata.tmdb.client import TmdbApiClient
from anivault.adapters.metadata.tmdb.mapper import tv_show_to_candidate
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO

_MAX_CANDIDATES = 5


class TmdbMetadataProvider:
    """TMDB TV 검색. 반환은 TmdbSeriesCandidateDTO만."""

    def __init__(self, client: TmdbApiClient) -> None:
        """TMDB API 클라이언트를 주입한다.

        Args:
            self: 이 인스턴스.
            client: 저수준 검색 클라이언트.

        Returns:
            None.
        """
        self._client = client

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        """제목·연도로 TV 시리즈 후보를 검색한다.

        Args:
            self: 이 공급자.
            query: 검색어.
            year: 첫 방영 연도 필터. None이면 무시.

        Returns:
            후보 DTO 시퀀스.
        """
        raw_list = self._client.search_tv_raw(
            query, first_air_date_year=year, max_results=_MAX_CANDIDATES
        )
        return [tv_show_to_candidate(obj) for obj in raw_list]
