"""TMDB HTTP access via tmdbapis. Used only inside this adapter package."""

from __future__ import annotations

from typing import Any

from tmdbapis import TMDbAPIs
from tmdbapis.exceptions import NotFound


class TmdbApiClient:
    """Thin wrapper: TV search with Korean-localized names."""

    def __init__(self, api_key: str, *, language: str = "ko-KR") -> None:
        self._api_key = api_key
        self._language = language
        self._tmdb: TMDbAPIs | None = None

    def _api(self) -> TMDbAPIs:
        """Lazy init: ``TMDbAPIs`` hits /configuration on construct — defer until first search."""
        if self._tmdb is None:
            self._tmdb = TMDbAPIs(apikey=self._api_key, language=self._language)
        return self._tmdb

    def search_tv_raw(
        self, query: str, *, first_air_date_year: int | None, max_results: int
    ) -> list[Any]:
        """
        Return up to ``max_results`` tmdbapis TVShow objects for the first page(s).
        Empty list if TMDB returns no hits.
        """
        q = (query or "").strip()
        if not q:
            return []
        try:
            pagination = self._api().tv_search(q, first_air_date_year=first_air_date_year)
        except NotFound:
            return []
        return list(pagination.get_results(amount=max_results))
