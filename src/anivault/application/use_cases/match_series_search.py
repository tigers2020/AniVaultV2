"""Search orchestration helpers for TMDB series matching."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from typing import Protocol

from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import (
    GroupMatchRepository,
    TmdbSeriesRepository,
)
from anivault.application.use_cases.match_series_persistence import (
    _match_single_group_apply_persist,
)
from anivault.application.use_cases.match_series_scoring import (
    _match_max_workers,
    _notify_match_progress_prepare,
    _notify_match_progress_step,
    _representative_path_norm_for_group,
    _select_best_candidate,
)
from anivault.application.use_cases.match_series_types import (
    MatchProgressCallback,
    TmdbCandidateProvenance,
)
from anivault.constants.application.statuses import (
    MATCH_STATUS_AUTO_MATCHED,
    MATCH_STATUS_CONFIRMED,
)
from anivault.constants.domain.matching import MATCH_REASON_CANCELLED
from anivault.contracts.pipeline import GroupMatchResult, PipelineRow
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.rules.tmdb_search_query import (
    iter_strip_last_word_chain,
    iter_tmdb_search_queries,
)


class _GroupMatchLookupRepository(GroupMatchRepository, TmdbSeriesRepository, Protocol):
    """Capabilities required for TMDB group lookup/search orchestration."""


def _try_series_from_title_match_db(
    *,
    root_id: int | None,
    representative_path_norm: str | None,
    title_match: _GroupMatchLookupRepository | None,
    title_groups: TitleGroupRepository | None,
) -> list[TmdbSeriesCandidate] | None:
    if (
        root_id is None
        or not representative_path_norm
        or title_match is None
        or title_groups is None
    ):
        return None
    group_id = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
    if group_id is None:
        return None
    group_match = title_match.get_group_match(group_id)
    if group_match is None or group_match.match_status not in (
        MATCH_STATUS_AUTO_MATCHED,
        MATCH_STATUS_CONFIRMED,
    ):
        return None
    candidate = title_match.get_series_candidate(group_match.tmdb_id)
    if candidate is None:
        return None
    return [candidate]


def _search_series_via_provider(
    group_key: str,
    provider: MetadataProvider,
) -> list[TmdbSeriesCandidate]:
    seen_attempts: set[str] = set()
    for query in iter_tmdb_search_queries(group_key):
        for attempt in iter_strip_last_word_chain(query):
            attempt_key = attempt.lower()
            if attempt_key in seen_attempts:
                continue
            seen_attempts.add(attempt_key)
            candidates = list(provider.search_series(attempt, year=None))
            if candidates:
                return candidates
    return []


def _search_series_candidates_for_group(
    group_key: str,
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: _GroupMatchLookupRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> tuple[list[TmdbSeriesCandidate], TmdbCandidateProvenance]:
    from_db = _try_series_from_title_match_db(
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    if from_db is not None:
        return from_db, "group_db"
    return _search_series_via_provider(group_key, provider), "provider"


def _match_single_group_search_phase(
    group_key: str,
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: _GroupMatchLookupRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> tuple[GroupMatchResult, TmdbSeriesCandidate | None, TmdbCandidateProvenance]:
    raw_candidates, provenance = _search_series_candidates_for_group(
        group_key,
        provider,
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    best, confidence, reason = _select_best_candidate(raw_candidates, group_key, "")
    if best is None or not best.tmdb_id:
        return (
            GroupMatchResult(
                group_key=group_key,
                matched=False,
                tmdb_id=None,
                korean_group_title="",
                original_title="",
                confidence=0.0,
                reason=reason,
            ),
            None,
            provenance,
        )
    return (
        GroupMatchResult(
            group_key=group_key,
            matched=bool((best.name_ko or "").strip()),
            tmdb_id=best.tmdb_id,
            korean_group_title=(best.name_ko or "").strip(),
            original_title=(best.original_name or "").strip(),
            confidence=confidence,
            reason=reason,
        ),
        best,
        provenance,
    )


def search_best_candidate_for_group(
    group_key: str,
    provider: MetadataProvider,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: _GroupMatchLookupRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
) -> tuple[GroupMatchResult, TmdbSeriesCandidate | None, TmdbCandidateProvenance]:
    return _match_single_group_search_phase(
        group_key,
        provider,
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )


def _search_one_group_for_parallel(
    files: list[PipelineRow],
    entry: tuple[str, list[int]],
    *,
    provider: MetadataProvider,
    root_scope: int | None,
    cancel_token: Event,
    title_match: _GroupMatchLookupRepository | None,
    title_groups: TitleGroupRepository | None,
) -> tuple[
    str,
    list[int],
    str | None,
    GroupMatchResult,
    TmdbSeriesCandidate | None,
    TmdbCandidateProvenance,
]:
    group_key, indices = entry
    path_norm = _representative_path_norm_for_group(files, root_scope, indices)
    if cancel_token.is_set():
        return (
            group_key,
            indices,
            path_norm,
            GroupMatchResult(
                group_key=group_key,
                matched=False,
                tmdb_id=None,
                korean_group_title="",
                original_title="",
                confidence=0.0,
                reason=MATCH_REASON_CANCELLED,
            ),
            None,
            "provider",
        )
    result, candidate, provenance = _match_single_group_search_phase(
        group_key,
        provider,
        root_id=root_scope,
        representative_path_norm=path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    return group_key, indices, path_norm, result, candidate, provenance


def _collect_group_match_results(
    files: list[PipelineRow],
    key_to_indices: dict[str, list[int]],
    *,
    provider: MetadataProvider,
    root_scope: int | None,
    progress_callback: MatchProgressCallback | None,
    cancel_token: Event,
    title_match: _GroupMatchLookupRepository | None,
    title_groups: TitleGroupRepository | None,
) -> list[GroupMatchResult]:
    items = list(key_to_indices.items())
    total = len(items)
    _notify_match_progress_prepare(progress_callback, total)
    group_results: list[GroupMatchResult] = []
    if not total:
        return group_results

    workers = _match_max_workers()
    if workers <= 1:
        ordered = [
            _search_one_group_for_parallel(
                files,
                entry,
                provider=provider,
                root_scope=root_scope,
                cancel_token=cancel_token,
                title_match=title_match,
                title_groups=title_groups,
            )
            for entry in items
        ]
    else:

        def _parallel_entry(
            entry: tuple[str, list[int]],
        ) -> tuple[
            str,
            list[int],
            str | None,
            GroupMatchResult,
            TmdbSeriesCandidate | None,
            TmdbCandidateProvenance,
        ]:
            return _search_one_group_for_parallel(
                files,
                entry,
                provider=provider,
                root_scope=root_scope,
                cancel_token=cancel_token,
                title_match=title_match,
                title_groups=title_groups,
            )

        with ThreadPoolExecutor(max_workers=workers) as pool:
            ordered = list(pool.map(_parallel_entry, items))

    for index, (group_key, indices, path_norm, result, candidate, _provenance) in enumerate(
        ordered
    ):
        if cancel_token.is_set():
            break
        _notify_match_progress_step(
            progress_callback,
            total,
            index + 1,
            f"TMDB search ({index + 1}/{total}): {group_key[:60]}",
        )
        if candidate is not None:
            _match_single_group_apply_persist(
                files,
                group_key,
                indices,
                candidate,
                result.confidence,
                root_id=root_scope,
                representative_path_norm=path_norm,
                title_match=title_match,
                title_groups=title_groups,
            )
        group_results.append(result)
    return group_results
