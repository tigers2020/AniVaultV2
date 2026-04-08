"""search_tv_library.py

GET /search/tv result row — docs/fixtures/tmdb_api/search_tv/_schema.json result_item_keys.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchTvLibraryRecord:
    """tmdb_search_tv_library 한 행. 배열 필드는 JSON 문자열."""

    tmdb_id: int
    language: str
    adult: bool
    backdrop_path: str | None
    genre_ids_json: str
    origin_country_json: str
    original_language: str
    original_name: str
    overview: str
    popularity: float
    poster_path: str | None
    first_air_date: str
    name: str
    vote_average: float
    vote_count: int
