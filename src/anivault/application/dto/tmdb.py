"""TMDB metadata DTOs. Filled by adapters; use cases consume these only."""

from dataclasses import dataclass


@dataclass(slots=True)
class TmdbSeriesCandidateDTO:
    """One TV series search candidate (localized fields per adapter request)."""

    tmdb_id: int
    name_ko: str
    original_name: str
    first_air_date: str
    original_language: str
    overview: str
    poster_path: str
    backdrop_path: str
    popularity: float
