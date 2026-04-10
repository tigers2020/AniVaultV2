from __future__ import annotations

from collections.abc import Sequence
from threading import Event
from typing import cast

from anivault.application.use_cases.fill_missing_cached_tmdb_matches import make_execute
from anivault.constants.gui.components import (
    PIPELINE_ROW_STATUS_TMDB_CACHED,
    PIPELINE_ROW_STATUS_TMDB_MATCHED,
)
from anivault.contracts.pipeline import MatchInput, MatchResult, PipelineRow
from anivault.contracts.title_groups import (
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)
from anivault.contracts.title_match import GroupTmdbMatchRecord, MatchStatus
from anivault.contracts.tmdb import TmdbSeriesCandidate


def _row(
    path: str,
    *,
    parsed: str = "Parsed",
    group: str = "Group",
    tmdb_id: str = "",
    ko_title: str = "",
    poster_path: str = "",
    poster_url: str = "",
) -> PipelineRow:
    return PipelineRow(
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


def _candidate(tmdb_id: int = 101) -> TmdbSeriesCandidate:
    return TmdbSeriesCandidate(
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
    def __init__(self, candidate: TmdbSeriesCandidate | None) -> None:
        self.candidate = candidate
        self.calls: list[str] = []

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidate]:
        del year
        self.calls.append(query)
        return [self.candidate] if self.candidate is not None else []


class _TitleGroups:
    def __init__(self, group_id: int = 7) -> None:
        self.group_id = group_id

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingRow]:
        del root_id
        return cast(list[TitleGroupingRow], [])

    def get_group_ids_for_path_norms(self, root_id: int, path_norms: list[str]) -> dict[str, int]:
        del root_id, path_norms
        return {}

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupBundle]) -> None:
        del root_id, bundles

    def replace_group_members(self, group_id: int, members: list[TitleGroupMember]) -> None:
        del group_id, members

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
        del root_id
        return cast(list[TitleGroupListRecord], [])

    def get_group_id(self, root_id: int, group_key: str) -> int | None:
        del root_id, group_key
        return None

    def get_group_id_for_path_norm(self, root_id: int, representative_path_norm: str) -> int | None:
        del root_id, representative_path_norm
        return self.group_id


class _TitleMatch:
    def __init__(self, *, group_match: GroupTmdbMatchRecord | None = None) -> None:
        self.upserts: list[int] = []
        self.poster_lookup: list[tuple[int, str, str]] = []
        self._group_match = group_match
        self._series_by_id: dict[int, TmdbSeriesCandidate] = {}

    def get_group_match(self, group_id: int) -> GroupTmdbMatchRecord | None:
        del group_id
        return self._group_match

    def get_search_cache_json(self, cache_key: str) -> str | None:
        del cache_key
        return None

    def put_search_cache(
        self,
        cache_key: str,
        *,
        language: str,
        normalized_query: str,
        year_hint: int | None,
        page: int,
        response_json: str,
        expires_at: str,
    ) -> None:
        del (
            cache_key,
            language,
            normalized_query,
            year_hint,
            page,
            response_json,
            expires_at,
        )

    def invalidate_search(self, cache_key: str) -> None:
        del cache_key

    def get_series_candidates(self, tmdb_ids: list[int]) -> dict[int, TmdbSeriesCandidate]:
        del tmdb_ids
        return {}

    def find_series_candidates_by_title(
        self, query: str, *, limit: int = 10
    ) -> list[TmdbSeriesCandidate]:
        del query, limit
        return []

    def get_group_matches(self, group_ids: list[int]) -> dict[int, GroupTmdbMatchRecord]:
        del group_ids
        return {}

    def set_series_for_group_db_test(self, tmdb_id: int, candidate: TmdbSeriesCandidate) -> None:
        self._series_by_id[tmdb_id] = candidate

    def set_group_match(
        self,
        group_id: int,
        tmdb_id: int,
        match_status: MatchStatus,
        match_score: float | None,
    ) -> None:
        del group_id, tmdb_id, match_status, match_score

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidate | None:
        return self._series_by_id.get(tmdb_id)

    def upsert_series(self, chosen: TmdbSeriesCandidate, *, raw_json: str, expires_at: str) -> None:
        del raw_json, expires_at
        self.upserts.append(chosen.tmdb_id)

    def invalidate_group_match(self, group_id: int) -> None:
        del group_id

    def save_poster_asset(
        self,
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
        *,
        local_path: str,
        status: str,
        verified_at: str | None,
    ) -> None:
        del tmdb_id, image_kind, remote_path, local_path, status, verified_at

    def get_poster_local_path(self, tmdb_id: int, image_kind: str, remote_path: str) -> str | None:
        self.poster_lookup.append((tmdb_id, image_kind, remote_path))
        return "F:/cache/poster.jpg"


def test_fill_missing_only_fetches_when_tmdb_metadata_missing() -> None:
    provider = _Provider(_candidate())
    title_match = _TitleMatch()
    execute = make_execute(
        provider=provider,
        title_match=title_match,
        title_groups=_TitleGroups(),
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
    assert result.files[0].status == PIPELINE_ROW_STATUS_TMDB_MATCHED
    assert result.files[1].tmdb_series_id == "55"
    assert result.files[1].tmdb_korean_title_group == "Already"


def test_fill_missing_does_not_call_provider_when_all_tmdb_metadata_exists() -> None:
    provider = _Provider(_candidate())
    execute = make_execute(
        provider=provider,
        title_match=_TitleMatch(),
        title_groups=_TitleGroups(),
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
        provider=provider,
        title_match=_TitleMatch(),
        title_groups=_TitleGroups(),
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


def test_fill_missing_uses_cached_status_when_candidate_from_group_db() -> None:
    cand = _candidate(303)
    gm = GroupTmdbMatchRecord(
        group_id=7,
        tmdb_id=303,
        match_status="auto_matched",
        match_score=0.9,
    )
    title_match = _TitleMatch(group_match=gm)
    title_match.set_series_for_group_db_test(303, cand)
    provider = _Provider(_candidate(999))
    execute = make_execute(
        provider=provider,
        title_match=title_match,
        title_groups=_TitleGroups(),
    )
    row = _row("a.mkv", group="Show")

    result = execute(
        MatchInput(files=(row,), index_root_id=1),
        progress_callback=None,
        cancel_token=Event(),
    )

    assert provider.calls == []
    assert result.files[0].tmdb_series_id == "303"
    assert result.files[0].tmdb_korean_title_group == "Korean"
    assert result.files[0].status == PIPELINE_ROW_STATUS_TMDB_CACHED
