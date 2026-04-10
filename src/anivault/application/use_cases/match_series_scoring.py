"""Scoring and grouping helpers for TMDB series matching."""

from __future__ import annotations

import os

from anivault.application.use_cases.match_series_types import MatchProgressCallback
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_MATCH
from anivault.constants.domain.matching import (
    MATCH_CONFIDENCE_FALLBACK,
    MATCH_REASON_EXACT_NAME,
    MATCH_REASON_FALLBACK_FIRST,
    MATCH_REASON_FIRST_RESULT,
    MATCH_REASON_NO_RESULTS,
    MATCH_REASON_PARTIAL_NAME,
    MATCH_SCORE_EXACT_NAME,
    MATCH_SCORE_LOCALIZED_NAME_BONUS,
    MATCH_SCORE_NORMALIZER,
    MATCH_SCORE_PARTIAL_NAME,
    MATCH_SCORE_POPULARITY_MULTIPLIER,
    MATCH_SCORE_YEAR_BONUS,
    TMDB_MAX_CANDIDATES,
)
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.progress import ProgressEvent
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.tmdb_search_query import compact_compare_key


def _group_key(row: PipelineRow) -> str:
    parse_group = (row.parse_group or "").strip()
    if parse_group:
        return parse_group
    parsed_title = (row.parsed_title or "").strip()
    if parsed_title:
        return parsed_title
    return row.original_file


def _year_prefix(iso_date: str) -> str:
    date_value = (iso_date or "").strip()
    return date_value[:4] if len(date_value) >= 4 else ""


def _score_one_candidate(
    candidate: TmdbSeriesCandidate,
    normalized_query: str,
    expected_year: str,
    reason_in: str,
) -> tuple[float, str]:
    score = 0.0
    reason = reason_in
    names = [
        compact_compare_key(candidate.name_ko),
        compact_compare_key(candidate.original_name),
    ]
    names = [name for name in names if name]
    if normalized_query and any(normalized_query == name for name in names):
        score += MATCH_SCORE_EXACT_NAME
        reason = MATCH_REASON_EXACT_NAME
    elif normalized_query and any(
        normalized_query in name or name in normalized_query for name in names
    ):
        score += MATCH_SCORE_PARTIAL_NAME
        reason = MATCH_REASON_PARTIAL_NAME
    if (candidate.name_ko or "").strip():
        score += MATCH_SCORE_LOCALIZED_NAME_BONUS
    candidate_year = _year_prefix(candidate.first_air_date)
    if expected_year and candidate_year == expected_year:
        score += MATCH_SCORE_YEAR_BONUS
        reason = f"{reason}+year"
    score += (candidate.popularity or 0.0) * MATCH_SCORE_POPULARITY_MULTIPLIER
    return score, reason


def _select_best_candidate(
    candidates: list[TmdbSeriesCandidate],
    query: str,
    expected_year: str,
) -> tuple[TmdbSeriesCandidate | None, float, str]:
    if not candidates:
        return None, 0.0, MATCH_REASON_NO_RESULTS
    normalized_query = compact_compare_key(query)
    best: TmdbSeriesCandidate | None = None
    best_score = -1.0
    reason = MATCH_REASON_FALLBACK_FIRST
    for candidate in candidates[:TMDB_MAX_CANDIDATES]:
        score, candidate_reason = _score_one_candidate(
            candidate,
            normalized_query,
            expected_year,
            reason,
        )
        if score > best_score:
            best_score = score
            best = candidate
            reason = candidate_reason
    if best is None:
        return candidates[0], MATCH_CONFIDENCE_FALLBACK, MATCH_REASON_FIRST_RESULT
    confidence = min(1.0, max(0.0, best_score / MATCH_SCORE_NORMALIZER))
    return best, confidence, reason


def _index_files_by_group_key(files: list[PipelineRow]) -> dict[str, list[int]]:
    key_to_indices: dict[str, list[int]] = {}
    for index, file_row in enumerate(files):
        key_to_indices.setdefault(_group_key(file_row), []).append(index)
    return key_to_indices


def _notify_match_progress_prepare(
    progress_callback: MatchProgressCallback | None,
    total: int,
) -> None:
    if not total or progress_callback is None:
        return
    progress_callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_MATCH,
            current=0,
            total=total,
            message="TMDB matching setup",
            percent=0,
        )
    )


def _notify_match_progress_step(
    progress_callback: MatchProgressCallback | None,
    total: int,
    current: int,
    message: str,
) -> None:
    if not total or progress_callback is None:
        return
    percent = int(current * PROGRESS_PERCENT_MAX / total) if total else PROGRESS_PERCENT_MAX
    progress_callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_MATCH,
            current=current,
            total=total,
            message=message,
            percent=percent,
        )
    )


def _representative_path_norm_for_group(
    files: list[PipelineRow],
    root_scope: int | None,
    indices: list[int],
) -> str | None:
    if root_scope is None or not indices:
        return None
    try:
        return normalize_path_key(files[indices[0]].original_file)
    except OSError:
        return None


def _match_max_workers() -> int:
    try:
        workers = int(os.environ.get("ANIVAULT_MATCH_MAX_WORKERS", "1"))
    except ValueError:
        workers = 1
    return max(1, min(8, workers))
