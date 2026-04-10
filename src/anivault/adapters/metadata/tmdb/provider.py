"""provider.py

tmdbapis 기반 MetadataProvider 구현.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from anivault.adapters.metadata.tmdb.client import TmdbApiClient
from anivault.adapters.metadata.tmdb.mapper import (
    tv_show_to_candidate,
    tv_show_to_search_tv_library_record,
)
from anivault.constants.domain.matching import TMDB_MAX_CANDIDATES
from anivault.contracts.tmdb import SearchTvLibraryRecord, TmdbSeriesCandidate


class TmdbMetadataProvider:
    """TMDB TV 검색. 반환은 TmdbSeriesCandidateDTO만."""

    def __init__(
        self,
        client: TmdbApiClient,
        *,
        persist_search_tv_library: Callable[[Sequence[SearchTvLibraryRecord]], None] | None = None,
    ) -> None:
        """TMDB API 클라이언트를 주입한다.

        Args:
            self: 이 인스턴스.
            client: 저수준 검색 클라이언트.
            persist_search_tv_library: 네트워크 검색 직후 원시 TV 행을 라이브러리에 기록할 때.

        Returns:
            None.
        """
        self._client = client
        self._persist_search_tv_library = persist_search_tv_library

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidate]:
        """제목·연도로 TV 시리즈 후보를 검색한다.

        Args:
            self: 이 공급자.
            query: 검색어.
            year: 첫 방영 연도 필터. None이면 무시.

        Returns:
            후보 DTO 시퀀스.
        """
        raw_list = self._client.search_tv_raw(
            query, first_air_date_year=year, max_results=TMDB_MAX_CANDIDATES
        )
        if self._persist_search_tv_library is not None and raw_list:
            lang = self._client.language
            self._persist_search_tv_library(
                [tv_show_to_search_tv_library_record(obj, lang) for obj in raw_list],
            )
        return [tv_show_to_candidate(obj) for obj in raw_list]
