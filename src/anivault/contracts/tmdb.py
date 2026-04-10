"""TMDB contracts."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TmdbSearchInput:
    """Input for TMDB search operations."""

    query: str
    year: int | None = None


@dataclass(slots=True, frozen=True)
class TmdbSeriesCandidate:
    """Normalized TMDB series candidate."""

    tmdb_id: int
    name_ko: str
    original_name: str
    first_air_date: str
    original_language: str
    overview: str
    poster_path: str
    backdrop_path: str
    popularity: float


@dataclass(frozen=True, slots=True)
class SearchTvLibraryRecord:
    """Read/write record for the cached TMDB search TV library."""

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
