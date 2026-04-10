from __future__ import annotations

import math
from threading import Event
from typing import cast

from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.application.use_cases import match_series
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_MATCHED
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.tmdb import TmdbSeriesCandidate


def _row(original: str, *, parsed: str = "", group: str = "") -> PipelineRow:
    return PipelineRow(
        original_file=original,
        parsed_title=parsed,
        parse_group=group,
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="1",
        resolution="FHD",
        status="pending",
        poster_url="",
        backdrop_url="",
        target_path="",
    )


def _candidate(
    tmdb_id: int = 1,
    *,
    name_ko: str = "Frieren",
    original_name: str = "Sousou no Frieren",
    first_air_date: str = "2023-09-29",
    poster_path: str = "/poster.jpg",
    backdrop_path: str = "/backdrop.jpg",
    popularity: float = 10.0,
) -> TmdbSeriesCandidate:
    return TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko=name_ko,
        original_name=original_name,
        first_air_date=first_air_date,
        original_language="ja",
        overview="",
        poster_path=poster_path,
        backdrop_path=backdrop_path,
        popularity=popularity,
    )


class _TitleMatchRepo:
    def __init__(
        self, candidate: TmdbSeriesCandidate | None = None, match: object | None = None
    ) -> None:
        self.candidate = candidate
        self.match = match
        self.upserts: list[int] = []
        self.group_matches: list[tuple[int, int, str, float | None]] = []

    def upsert_series(self, chosen: TmdbSeriesCandidate, *, raw_json: str, expires_at: str) -> None:
        self.upserts.append(chosen.tmdb_id)

    def set_group_match(
        self, group_id: int, tmdb_id: int, status: str, score: float | None
    ) -> None:
        self.group_matches.append((group_id, tmdb_id, status, score))

    def get_group_match(self, group_id: int) -> object | None:
        return self.match

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidate | None:
        return self.candidate


class _TitleGroupsRepo:
    def __init__(self, group_id: int | None) -> None:
        self.group_id = group_id

    def get_group_id_for_path_norm(self, root_id: int, representative_path_norm: str) -> int | None:
        return self.group_id


def test_group_key_prefers_parse_group_then_title_then_original_file() -> None:
    assert match_series._group_key(_row("file.mkv", parsed="Parsed", group="Group")) == "Group"
    assert match_series._group_key(_row("file.mkv", parsed="Parsed", group="")) == "Parsed"
    assert match_series._group_key(_row("file.mkv")) == "file.mkv"


def test_score_one_candidate_applies_exact_and_year_bonus() -> None:
    score, reason = match_series._score_one_candidate(
        _candidate(),
        "frieren",
        "2023",
        "fallback",
    )

    assert score > 0
    assert reason == "exact_name+year"


def test_select_best_candidate_returns_fallback_for_empty_candidates() -> None:
    best, confidence, reason = match_series._select_best_candidate([], "query", "")

    assert best is None
    assert math.isclose(confidence, 0.0)
    assert reason == "no_results"


def test_select_best_candidate_prefers_stronger_match() -> None:
    low = _candidate(1, name_ko="Other", original_name="Other", popularity=0.0)
    high = _candidate(2, popularity=1.0)

    best, confidence, reason = match_series._select_best_candidate([low, high], "Frieren", "2023")

    assert best == high
    assert confidence > 0
    assert reason == "exact_name+year"


def test_index_files_by_group_key_groups_indices() -> None:
    grouped = match_series._index_files_by_group_key(
        [_row("a.mkv", group="A"), _row("b.mkv", group="A"), _row("c.mkv", parsed="C")]
    )

    assert grouped == {"A": [0, 1], "C": [2]}


def test_notify_match_progress_helpers_emit_expected_events() -> None:
    events = []

    match_series._notify_match_progress_prepare(events.append, 2)
    match_series._notify_match_progress_step(events.append, 2, 1, "done")

    assert [(e.current, e.total, e.message) for e in events] == [
        (0, 2, "TMDB matching setup"),
        (1, 2, "done"),
    ]


def test_apply_tmdb_candidate_to_file_rows_updates_selected_rows() -> None:
    files = [_row("a.mkv"), _row("b.mkv", parsed="Parsed")]

    match_series.apply_tmdb_candidate_to_file_rows(files, [1], _candidate(99))

    assert files[0].tmdb_series_id == ""
    assert files[1].tmdb_series_id == "99"
    assert files[1].tmdb_korean_title_group == "Frieren"
    assert files[1].status == PIPELINE_ROW_STATUS_TMDB_MATCHED


def test_persist_manual_tmdb_selection_requires_valid_dependencies() -> None:
    files = [_row("a.mkv")]
    repo = _TitleMatchRepo()

    match_series.persist_manual_tmdb_selection(
        files,
        [0],
        _candidate(10),
        root_id=None,
        representative_path_norm=None,
        title_match=cast(TitleMatchRepository, repo),
        title_groups=None,
    )

    assert repo.upserts == [10]
    assert repo.group_matches == []


def test_try_series_from_title_match_db_returns_short_circuit_candidate() -> None:
    group_match = type("GroupMatch", (), {"tmdb_id": 7, "match_status": "confirmed"})()
    title_match = _TitleMatchRepo(candidate=_candidate(7), match=group_match)

    result = match_series._try_series_from_title_match_db(
        root_id=1,
        representative_path_norm="f:/anime/show.mkv",
        title_match=cast(TitleMatchRepository, title_match),
        title_groups=cast(TitleGroupRepository, _TitleGroupsRepo(5)),
    )

    assert result == [_candidate(7)]


def test_search_series_via_provider_uses_word_stripping_until_hit() -> None:
    class _Provider:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def search_series(self, query: str, year: int | None = None):
            self.calls.append(query)
            if query == "Frieren":
                return [_candidate()]
            return []

    provider = _Provider()

    result = match_series._search_series_via_provider("Frieren Extra Word", provider)

    assert result == [_candidate()]
    assert provider.calls == ["Frieren Extra Word", "Frieren Extra", "Frieren"]


def test_match_single_group_search_phase_returns_miss_dto() -> None:
    class _Provider:
        def search_series(self, query: str, year: int | None = None):
            return []

    dto, candidate, provenance = match_series._match_single_group_search_phase(
        "Unknown", _Provider()
    )

    assert candidate is None
    assert provenance == "provider"
    assert dto.matched is False
    assert dto.reason == "no_results"


def test_match_single_group_apply_persist_updates_files_and_db() -> None:
    files = [_row("a.mkv", group="Frieren")]
    title_match = _TitleMatchRepo(match=None)

    match_series._match_single_group_apply_persist(
        files,
        "Frieren",
        [0],
        _candidate(4),
        0.8,
        root_id=1,
        representative_path_norm="f:/anime/a.mkv",
        title_match=cast(TitleMatchRepository, title_match),
        title_groups=cast(TitleGroupRepository, _TitleGroupsRepo(11)),
    )

    assert files[0].tmdb_series_id == "4"
    assert title_match.upserts == [4]
    assert title_match.group_matches == [(11, 4, "auto_matched", 0.8)]


def test_representative_path_norm_for_group_handles_errors(monkeypatch) -> None:
    files = [_row("a.mkv")]

    def _normalize_raises(path: object) -> str:
        raise OSError()

    monkeypatch.setattr(match_series, "normalize_path_key", _normalize_raises)

    assert match_series._representative_path_norm_for_group(files, 1, [0]) is None


def test_match_max_workers_clamps_environment(monkeypatch) -> None:
    monkeypatch.setenv("ANIVAULT_MATCH_MAX_WORKERS", "99")
    assert match_series._match_max_workers() == 8
    monkeypatch.setenv("ANIVAULT_MATCH_MAX_WORKERS", "bad")
    assert match_series._match_max_workers() == 1


def test_search_one_group_for_parallel_returns_cancelled_dto() -> None:
    token = Event()
    token.set()

    key, indices, path_norm, dto, candidate, provenance = (
        match_series._search_one_group_for_parallel(
            [_row("a.mkv", group="A")],
            ("A", [0]),
            provider=None,  # type: ignore[arg-type]
            root_scope=1,
            cancel_token=token,
            title_match=None,
            title_groups=None,
        )
    )

    assert (key, indices, candidate) == ("A", [0], None)
    assert provenance == "provider"
    assert path_norm is not None
    assert dto.reason == "cancelled"
