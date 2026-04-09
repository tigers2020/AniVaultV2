from __future__ import annotations

from datetime import date

from anivault.adapters.metadata.tmdb.mapper import (
    _as_str,
    _first_air_date_str,
    tv_show_to_candidate,
)


class _Lang:
    iso_639_1 = "ja"


class _TvShow:
    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_as_str_prefers_iso_code_attribute() -> None:
    assert _as_str(_Lang()) == "ja"
    assert _as_str(None) == ""


def test_first_air_date_str_formats_date_like_values() -> None:
    assert _first_air_date_str(_TvShow(first_air_date=date(2024, 1, 2))) == "2024-01-02"
    assert _first_air_date_str(_TvShow(first_air_date=None)) == ""


def test_tv_show_to_candidate_coerces_invalid_fields_to_safe_defaults() -> None:
    candidate = tv_show_to_candidate(
        _TvShow(
            id="bad",
            title="Fallback Title",
            original_name=None,
            first_air_date="2024-03-04",
            original_language=_Lang(),
            overview=None,
            poster_path=None,
            backdrop_path="/backdrop.jpg",
            popularity="bad",
        )
    )

    assert candidate.tmdb_id == 0
    assert candidate.name_ko == "Fallback Title"
    assert candidate.original_name == ""
    assert candidate.first_air_date == "2024-03-04"
    assert candidate.original_language == "ja"
    assert candidate.overview == ""
    assert candidate.poster_path == ""
    assert candidate.backdrop_path == "/backdrop.jpg"
    assert candidate.popularity == 0.0
