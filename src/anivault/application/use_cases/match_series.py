"""TMDB series matching use case composed from focused helper modules."""

from __future__ import annotations

from collections.abc import Callable
from threading import Event

from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.application.use_cases.match_series_persistence import (
    _apply_tmdb_to_file_rows,
    _match_single_group_apply_persist,
    _utc_plus_days_iso_z,
    apply_candidate_and_persist_for_group,
    apply_tmdb_candidate_to_file_rows,
    persist_manual_tmdb_selection,
)
from anivault.application.use_cases.match_series_scoring import (
    _group_key,
    _index_files_by_group_key,
    _match_max_workers,
    _notify_match_progress_prepare,
    _notify_match_progress_step,
    _score_one_candidate,
    _select_best_candidate,
    _year_prefix,
)
from anivault.application.use_cases.match_series_search import (
    _collect_group_match_results,
    _match_single_group_search_phase,
    _search_one_group_for_parallel,
    _search_series_candidates_for_group,
    _search_series_via_provider,
    _try_series_from_title_match_db,
    search_best_candidate_for_group,
)
from anivault.application.use_cases.match_series_types import (
    MatchProgressCallback,
    TmdbCandidateProvenance,
)
from anivault.contracts.pipeline import MatchInput, MatchResult, PipelineRow
from anivault.domain.path_norm import normalize_path_key

__all__ = [
    "_apply_tmdb_to_file_rows",
    "_collect_group_match_results",
    "_group_key",
    "_index_files_by_group_key",
    "_match_max_workers",
    "_match_single_group_apply_persist",
    "_match_single_group_search_phase",
    "_notify_match_progress_prepare",
    "_notify_match_progress_step",
    "_representative_path_norm_for_group",
    "_score_one_candidate",
    "_search_one_group_for_parallel",
    "_search_series_candidates_for_group",
    "_search_series_via_provider",
    "_select_best_candidate",
    "_try_series_from_title_match_db",
    "_utc_plus_days_iso_z",
    "_year_prefix",
    "MatchProgressCallback",
    "TmdbCandidateProvenance",
    "apply_candidate_and_persist_for_group",
    "apply_tmdb_candidate_to_file_rows",
    "make_execute",
    "normalize_path_key",
    "persist_manual_tmdb_selection",
    "search_best_candidate_for_group",
]


def _representative_path_norm_for_group(
    files: list[PipelineRow],
    root_scope: int | None,
    indices: list[int],
) -> str | None:
    """Compatibility wrapper kept for tests that monkeypatch module globals."""

    if root_scope is None or not indices:
        return None
    try:
        return normalize_path_key(str(files[indices[0]].original_file))
    except OSError:
        return None


def make_execute(
    provider: MetadataProvider,
    *,
    title_match: TitleMatchRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
    poster_sync: Callable[[MatchResult], None] | None = None,
) -> Callable[[MatchInput, MatchProgressCallback | None, Event], MatchResult]:
    """Create the TMDB match use case."""

    def execute(
        input_dto: MatchInput,
        progress_callback: MatchProgressCallback | None,
        cancel_token: Event,
    ) -> MatchResult:
        files = list(input_dto.files)
        if cancel_token.is_set():
            return MatchResult(files=tuple(files), groups=())

        key_to_indices = _index_files_by_group_key(files)
        group_results = _collect_group_match_results(
            files,
            key_to_indices,
            provider=provider,
            root_scope=input_dto.index_root_id,
            progress_callback=progress_callback,
            cancel_token=cancel_token,
            title_match=title_match,
            title_groups=title_groups,
        )

        result = MatchResult(files=tuple(files), groups=tuple(group_results))
        if poster_sync is not None:
            poster_sync(result)
        return result

    return execute
