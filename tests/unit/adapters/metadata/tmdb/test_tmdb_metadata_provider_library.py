"""TmdbMetadataProvider persists search rows when callback is set."""

from __future__ import annotations

from types import SimpleNamespace

from anivault.adapters.metadata.tmdb.provider import TmdbMetadataProvider
from anivault.application.dto.search_tv_library import SearchTvLibraryRecord


def test_search_series_invokes_persist_with_mapped_records() -> None:
    raw = SimpleNamespace(
        adult=False,
        backdrop_path="/b.jpg",
        genre_ids=[1, 2],
        origin_country=["JP"],
        id=99,
        original_language="ja",
        original_name="Orig",
        overview="ov",
        popularity=5.5,
        poster_path="/p.jpg",
        first_air_date="2021-01-02",
        name="로컬",
        vote_average=7.0,
        vote_count=100,
    )

    class _Client:
        language = "ko-KR"

        def search_tv_raw(
            self,
            query: str,
            *,
            first_air_date_year: int | None,
            max_results: int,
        ) -> list[object]:
            del query, first_air_date_year, max_results
            return [raw]

    captured: list[SearchTvLibraryRecord] = []

    def _persist(recs: list[SearchTvLibraryRecord]) -> None:
        captured.extend(recs)

    provider = TmdbMetadataProvider(_Client(), persist_search_tv_library=_persist)
    out = provider.search_series("q", year=None)
    assert len(out) == 1
    assert len(captured) == 1
    assert captured[0].tmdb_id == 99
    assert captured[0].language == "ko-KR"
    assert captured[0].name == "로컬"


def test_search_series_skips_persist_when_empty_raw() -> None:
    class _Client:
        language = "en-US"

        def search_tv_raw(
            self,
            query: str,
            *,
            first_air_date_year: int | None,
            max_results: int,
        ) -> list[object]:
            return []

    called = False

    def _persist(_: object) -> None:
        nonlocal called
        called = True

    provider = TmdbMetadataProvider(_Client(), persist_search_tv_library=_persist)
    assert provider.search_series("none", year=None) == []
    assert called is False
