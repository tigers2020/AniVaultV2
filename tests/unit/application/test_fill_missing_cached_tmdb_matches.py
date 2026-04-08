from __future__ import annotations

from threading import Event

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.use_cases.fill_missing_cached_tmdb_matches import make_execute


def _row(
    path: str,
    *,
    parsed: str = "Parsed",
    group: str = "Group",
    tmdb_id: str = "",
    ko_title: str = "",
    poster_path: str = "",
    poster_url: str = "",
) -> MatchFileRow:
    return MatchFileRow(
        original_file=path,
        parsed_title=parsed,
        parse_group=group,
        tmdb_korean_title_group=ko_title,
        tmdb_series_id=tmdb_id,
        tmdb_poster_path=poster_path,
        tmdb_backdrop_path="",
        year="",
        season="1",
        resolution="1080p",
        status="parsed",
        poster_url=poster_url,
        backdrop_url="",
        target_path="",
        episode="01",
    )


def _candidate(tmdb_id: int = 101) -> TmdbSeriesCandidateDTO:
    return TmdbSeriesCandidateDTO(
        tmdb_id=tmdb_id,
        name_ko="Korean",
        original_name="Original",
        first_air_date="2024-01-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )


class _Provider:
    def __init__(self, candidate: TmdbSeriesCandidateDTO | None) -> None:
        self.candidate = candidate
        self.calls: list[str] = []

    def search_series(self, query: str, year: int | None = None) -> list[TmdbSeriesCandidateDTO]:
        del year
        self.calls.append(query)
        return [self.candidate] if self.candidate is not None else []


class _TitleGroups:
    def __init__(self, group_id: int = 7) -> None:
        self.group_id = group_id

    def get_group_id_for_path_norm(self, root_id: int, representative_path_norm: str) -> int | None:
        del root_id, representative_path_norm
        return self.group_id


class _TitleMatch:
    def __init__(self) -> None:
        self.upserts: list[int] = []
        self.poster_lookup: list[tuple[int, str, str]] = []

    def get_group_match(self, group_id: int):
        del group_id
        return None

    def set_group_match(
        self, group_id: int, tmdb_id: int, status: str, score: float | None
    ) -> None:
        del group_id, tmdb_id, status, score

    def get_series_candidate(self, tmdb_id: int):
        del tmdb_id
        return None

    def upsert_series(
        self, chosen: TmdbSeriesCandidateDTO, *, raw_json: str, expires_at: str
    ) -> None:
        del raw_json, expires_at
        self.upserts.append(chosen.tmdb_id)

    def get_poster_local_path(self, tmdb_id: int, image_kind: str, remote_path: str) -> str | None:
        self.poster_lookup.append((tmdb_id, image_kind, remote_path))
        return "F:/cache/poster.jpg"


def test_fill_missing_only_fetches_when_tmdb_metadata_missing() -> None:
    provider = _Provider(_candidate())
    title_match = _TitleMatch()
    execute = make_execute(
        provider=provider,  # type: ignore[arg-type]
        title_match=title_match,  # type: ignore[arg-type]
        title_groups=_TitleGroups(),  # type: ignore[arg-type]
    )
    existing = _row(
        "b.mkv",
        group="AnotherGroup",
        tmdb_id="55",
        ko_title="Already",
        poster_path="/p.jpg",
        poster_url="https://example.com/p.jpg",
    )
    missing = _row("a.mkv")

    result = execute(
        MatchInput(files=(missing, existing), index_root_id=1),
        progress_callback=None,
        cancel_token=Event(),
    )

    assert provider.calls
    assert result.files[0].tmdb_series_id == "101"
    assert result.files[0].tmdb_korean_title_group == "Korean"
    assert result.files[1].tmdb_series_id == "55"
    assert result.files[1].tmdb_korean_title_group == "Already"


def test_fill_missing_does_not_call_provider_when_all_tmdb_metadata_exists() -> None:
    provider = _Provider(_candidate())
    execute = make_execute(
        provider=provider,  # type: ignore[arg-type]
        title_match=_TitleMatch(),  # type: ignore[arg-type]
        title_groups=_TitleGroups(),  # type: ignore[arg-type]
    )
    ready = _row(
        "a.mkv",
        tmdb_id="55",
        ko_title="Already",
        poster_path="/p.jpg",
        poster_url="https://example.com/p.jpg",
    )

    result = execute(
        MatchInput(files=(ready,), index_root_id=1),
        progress_callback=None,
        cancel_token=Event(),
    )

    assert provider.calls == []
    assert result.files == (ready,)


def test_fill_missing_calls_poster_sync_only_for_rows_with_missing_poster() -> None:
    provider = _Provider(None)
    poster_calls: list[tuple[MatchResult, ...]] = []
    execute = make_execute(
        provider=provider,  # type: ignore[arg-type]
        title_match=_TitleMatch(),  # type: ignore[arg-type]
        title_groups=_TitleGroups(),  # type: ignore[arg-type]
        poster_sync=lambda result: poster_calls.append((result,)),
    )
    row_missing_poster = _row(
        "a.mkv", tmdb_id="11", ko_title="Filled", poster_path="/p.jpg", poster_url=""
    )
    row_ready = _row(
        "b.mkv",
        tmdb_id="12",
        ko_title="Filled",
        poster_path="/p2.jpg",
        poster_url="https://example.com/p2.jpg",
    )

    execute(
        MatchInput(files=(row_missing_poster, row_ready), index_root_id=1),
        progress_callback=None,
        cancel_token=Event(),
    )

    assert len(poster_calls) == 1
    synced = poster_calls[0][0]
    assert [row.original_file for row in synced.files] == ["a.mkv"]
