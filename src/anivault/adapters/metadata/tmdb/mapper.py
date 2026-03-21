"""Map tmdbapis objects to application DTOs."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "iso_639_1"):
        raw = getattr(value, "iso_639_1", None)
        return str(raw) if raw is not None else ""
    return str(value)


def _first_air_date_str(tv: Any) -> str:
    raw = getattr(tv, "first_air_date", None)
    if raw is None:
        return ""
    if isinstance(raw, (date, datetime)):
        return raw.strftime("%Y-%m-%d")
    return str(raw)


def tv_show_to_candidate(tv: Any) -> TmdbSeriesCandidateDTO:
    """Build DTO from a tmdbapis TVShow (including partial search results)."""
    tid_raw = getattr(tv, "id", 0)
    try:
        tmdb_id = int(tid_raw)
    except (TypeError, ValueError):
        tmdb_id = 0

    pop_raw = getattr(tv, "popularity", 0) or 0
    try:
        popularity = float(pop_raw)
    except (TypeError, ValueError):
        popularity = 0.0

    poster = getattr(tv, "poster_path", None)
    poster_path = str(poster) if poster else ""

    backdrop = getattr(tv, "backdrop_path", None)
    backdrop_path = str(backdrop) if backdrop else ""

    return TmdbSeriesCandidateDTO(
        tmdb_id=tmdb_id,
        name_ko=_as_str(getattr(tv, "name", None) or getattr(tv, "title", None)),
        original_name=_as_str(getattr(tv, "original_name", None)),
        first_air_date=_first_air_date_str(tv),
        original_language=_as_str(getattr(tv, "original_language", None)),
        overview=_as_str(getattr(tv, "overview", None)),
        poster_path=poster_path,
        backdrop_path=backdrop_path,
        popularity=popularity,
    )
