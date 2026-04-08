"""tv_show_to_search_tv_library_record from fixture-shaped namespace objects."""

from __future__ import annotations

import json
from types import SimpleNamespace

from anivault.adapters.metadata.tmdb.mapper import tv_show_to_search_tv_library_record


def test_mapper_matches_spy_x_family_first_result_shape() -> None:
    tv = SimpleNamespace(
        adult=False,
        backdrop_path="/lysUnU6V0VfcthDbviuVlIqgHOR.jpg",
        genre_ids=[16, 10759, 35],
        id=120089,
        origin_country=["JP"],
        original_language="ja",
        original_name="SPY×FAMILY",
        overview="short",
        popularity=123.183,
        poster_path="/rikBBQHmCTOiZ7YoJVkYcKdXgNx.jpg",
        first_air_date="2022-04-09",
        name="스파이 패밀리",
        vote_average=8.511,
        vote_count=2213,
    )
    r = tv_show_to_search_tv_library_record(tv, "ko-KR")
    assert r.tmdb_id == 120089
    assert r.language == "ko-KR"
    assert r.adult is False
    assert r.backdrop_path == "/lysUnU6V0VfcthDbviuVlIqgHOR.jpg"
    assert json.loads(r.genre_ids_json) == [16, 10759, 35]
    assert json.loads(r.origin_country_json) == ["JP"]
    assert r.original_language == "ja"
    assert r.original_name == "SPY×FAMILY"
    assert r.overview == "short"
    assert r.popularity == 123.183
    assert r.poster_path == "/rikBBQHmCTOiZ7YoJVkYcKdXgNx.jpg"
    assert r.first_air_date == "2022-04-09"
    assert r.name == "스파이 패밀리"
    assert r.vote_average == 8.511
    assert r.vote_count == 2213


def test_mapper_null_poster_becomes_none() -> None:
    tv = SimpleNamespace(
        adult=False,
        backdrop_path=None,
        genre_ids=[],
        id=1,
        origin_country=[],
        original_language="en",
        original_name="A",
        overview="",
        popularity=1.0,
        poster_path=None,
        first_air_date="",
        name="A",
        vote_average=0.0,
        vote_count=0,
    )
    r = tv_show_to_search_tv_library_record(tv, "en-US")
    assert r.poster_path is None
    assert r.backdrop_path is None
