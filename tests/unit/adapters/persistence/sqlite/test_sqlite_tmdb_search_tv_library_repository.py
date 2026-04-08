"""Round-trip tmdb_search_tv_library vs docs/fixtures/tmdb_api/search_tv."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

import pytest

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_tmdb_search_tv_library_repository import (
    SqliteTmdbSearchTvLibraryRepository,
)
from anivault.application.dto.search_tv_library import SearchTvLibraryRecord

_REPO_ROOT = Path(__file__).resolve().parents[5]
_FIXTURE_DIR = _REPO_ROOT / "docs" / "fixtures" / "tmdb_api" / "search_tv"


def _record_from_fixture_item(d: dict, language: str) -> SearchTvLibraryRecord:
    return SearchTvLibraryRecord(
        tmdb_id=int(d["id"]),
        language=language,
        adult=bool(d["adult"]),
        backdrop_path=d.get("backdrop_path"),
        genre_ids_json=json.dumps(d["genre_ids"], separators=(",", ":")),
        origin_country_json=json.dumps(
            d["origin_country"],
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        original_language=str(d.get("original_language", "") or ""),
        original_name=str(d.get("original_name", "") or ""),
        overview=str(d.get("overview", "") or ""),
        popularity=float(d.get("popularity", 0) or 0),
        poster_path=d.get("poster_path"),
        first_air_date=str(d.get("first_air_date", "") or ""),
        name=str(d.get("name", "") or ""),
        vote_average=float(d.get("vote_average", 0) or 0),
        vote_count=int(d.get("vote_count", 0) or 0),
    )


def _assert_row_matches_fixture(got: SearchTvLibraryRecord, item: dict, language: str) -> None:
    assert got.tmdb_id == int(item["id"])
    assert got.language == language
    assert got.adult == bool(item["adult"])
    assert got.backdrop_path == item.get("backdrop_path")
    assert json.loads(got.genre_ids_json) == item["genre_ids"]
    assert json.loads(got.origin_country_json) == item["origin_country"]
    assert got.original_language == str(item.get("original_language", "") or "")
    assert got.original_name == str(item.get("original_name", "") or "")
    assert got.overview == str(item.get("overview", "") or "")
    assert got.popularity == pytest.approx(float(item.get("popularity", 0) or 0))
    assert got.poster_path == item.get("poster_path")
    assert got.first_air_date == str(item.get("first_air_date", "") or "")
    assert got.name == str(item.get("name", "") or "")
    assert got.vote_average == pytest.approx(float(item.get("vote_average", 0) or 0))
    assert got.vote_count == int(item.get("vote_count", 0) or 0)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "spy_x_family.json",
        "attack_on_titan.json",
        "chainsaw_man.json",
        "cowboy_bebop.json",
        "demon_slayer.json",
        "jujutsu_kaisen.json",
        "naruto_shippuden.json",
        "one_piece.json",
    ],
)
def test_fixture_round_trip(tmp_path: Path, fixture_name: str) -> None:
    path = _FIXTURE_DIR / fixture_name
    data = json.loads(path.read_text(encoding="utf-8"))
    language = str(data["_meta"]["language"])
    conn = create_connection(tmp_path / "tmdb_library.db")
    try:
        lock = Lock()
        repo = SqliteTmdbSearchTvLibraryRepository(conn, lock)
        for item in data["response"]["results"]:
            rec = _record_from_fixture_item(item, language)
            repo.upsert(rec)
            got = repo.get(rec.tmdb_id, language)
            assert got is not None
            _assert_row_matches_fixture(got, item, language)
    finally:
        conn.close()
