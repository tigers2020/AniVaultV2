"""MetadataProvider implementation backed by tmdbapis."""

from __future__ import annotations

from collections.abc import Sequence

from anivault.adapters.metadata.tmdb.client import TmdbApiClient
from anivault.adapters.metadata.tmdb.mapper import tv_show_to_candidate
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO

_MAX_CANDIDATES = 5


class TmdbMetadataProvider:
    """TMDB TV search; returns only ``TmdbSeriesCandidateDTO`` instances."""

    def __init__(self, client: TmdbApiClient) -> None:
        self._client = client

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        raw_list = self._client.search_tv_raw(
            query, first_air_date_year=year, max_results=_MAX_CANDIDATES
        )
        return [tv_show_to_candidate(obj) for obj in raw_list]
