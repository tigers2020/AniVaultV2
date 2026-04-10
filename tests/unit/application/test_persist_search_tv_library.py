"""persist_search_tv_library use case."""

from __future__ import annotations

from anivault.application.use_cases.persist_search_tv_library import make_execute
from anivault.contracts.tmdb import SearchTvLibraryRecord


def _sample_record(*, tmdb_id: int = 1) -> SearchTvLibraryRecord:
    return SearchTvLibraryRecord(
        tmdb_id=tmdb_id,
        language="ko-KR",
        adult=False,
        backdrop_path=None,
        genre_ids_json="[]",
        origin_country_json="[]",
        original_language="ja",
        original_name="X",
        overview="",
        popularity=1.0,
        poster_path=None,
        first_air_date="2020-01-01",
        name="엑스",
        vote_average=8.0,
        vote_count=10,
    )


def test_persist_skips_non_positive_tmdb_id() -> None:
    stored: list[SearchTvLibraryRecord] = []

    class _Repo:
        def upsert(self, r: SearchTvLibraryRecord) -> None:
            stored.append(r)

        def get(self, tmdb_id: int, language: str) -> SearchTvLibraryRecord | None:
            return None

    ex = make_execute(_Repo())
    ex([_sample_record(tmdb_id=0), _sample_record(tmdb_id=-1)])
    assert stored == []


def test_persist_upserts_valid_rows() -> None:
    stored: list[SearchTvLibraryRecord] = []

    class _Repo:
        def upsert(self, r: SearchTvLibraryRecord) -> None:
            stored.append(r)

        def get(self, tmdb_id: int, language: str) -> SearchTvLibraryRecord | None:
            return None

    ex = make_execute(_Repo())
    a = _sample_record(tmdb_id=120089)
    b = _sample_record(tmdb_id=6929)
    ex([a, b])
    assert stored == [a, b]
