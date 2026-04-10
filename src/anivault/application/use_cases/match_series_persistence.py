"""Persistence helpers for TMDB series matching."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from typing import Protocol, cast

from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import (
    GroupMatchRepository,
    TmdbSeriesRepository,
)
from anivault.constants.application.statuses import (
    MATCH_STATUS_AUTO_MATCHED,
    MATCH_STATUS_CONFIRMED,
)
from anivault.constants.domain.matching import TMDB_SERIES_CACHE_TTL_DAYS
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_MATCHED
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.title_match import MatchStatus
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.rules.tmdb_image_url import tmdb_backdrop_cdn_url, tmdb_poster_cdn_url

logger = logging.getLogger(__name__)


class _MatchPersistenceRepository(TmdbSeriesRepository, GroupMatchRepository, Protocol):
    """Capabilities required to persist TMDB matches."""


def _utc_plus_days_iso_z(days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _apply_tmdb_to_file_rows(
    files: list[PipelineRow],
    indices: list[int],
    candidate: TmdbSeriesCandidate,
    *,
    korean_row_status: str | None = None,
) -> None:
    korean_title = (candidate.name_ko or "").strip()
    poster_path = (candidate.poster_path or "").strip()
    backdrop_path = (candidate.backdrop_path or "").strip()
    poster_url = tmdb_poster_cdn_url(poster_path)
    backdrop_url = tmdb_backdrop_cdn_url(backdrop_path)
    tmdb_series_id = str(candidate.tmdb_id)
    tmdb_year = (candidate.first_air_date or "").strip()[:4]
    status_when_korean = (
        PIPELINE_ROW_STATUS_TMDB_MATCHED if korean_row_status is None else korean_row_status
    )
    for index in indices:
        previous = files[index]
        files[index] = replace(
            previous,
            tmdb_korean_title_group=korean_title or previous.tmdb_korean_title_group,
            tmdb_series_id=tmdb_series_id,
            tmdb_poster_path=poster_path or previous.tmdb_poster_path,
            tmdb_backdrop_path=backdrop_path or previous.tmdb_backdrop_path,
            year=tmdb_year or previous.year,
            status=status_when_korean if korean_title else previous.status,
            poster_url=poster_url or previous.poster_url,
            backdrop_url=backdrop_url or previous.backdrop_url,
        )


def apply_tmdb_candidate_to_file_rows(
    files: list[PipelineRow],
    indices: list[int],
    candidate: TmdbSeriesCandidate,
    *,
    korean_status: str | None = None,
) -> None:
    _apply_tmdb_to_file_rows(files, indices, candidate, korean_row_status=korean_status)


def persist_manual_tmdb_selection(
    files: list[PipelineRow],
    indices: list[int],
    chosen: TmdbSeriesCandidate,
    *,
    root_id: int | None,
    representative_path_norm: str | None,
    title_match: _MatchPersistenceRepository | None,
    title_groups: TitleGroupRepository | None,
) -> None:
    if title_match is None or not indices or max(indices) >= len(files):
        return
    if not chosen.tmdb_id:
        return
    raw_json = json.dumps(asdict(chosen), ensure_ascii=False, separators=(",", ":"))
    expires_at = _utc_plus_days_iso_z(TMDB_SERIES_CACHE_TTL_DAYS)
    try:
        title_match.upsert_series(chosen, raw_json=raw_json, expires_at=expires_at)
    except Exception:
        logger.exception("manual TMDB tmdb_series upsert failed tmdb_id=%s", chosen.tmdb_id)
        return
    if root_id is None or not representative_path_norm or title_groups is None:
        return
    group_id = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
    if group_id is None:
        logger.warning(
            "manual TMDB: no title group for path root_id=%s path_norm=%s",
            root_id,
            representative_path_norm,
        )
        return
    try:
        title_match.set_group_match(
            group_id,
            int(chosen.tmdb_id),
            cast(MatchStatus, MATCH_STATUS_CONFIRMED),
            None,
        )
    except Exception:
        logger.exception(
            "manual TMDB group persist failed group_id=%s tmdb_id=%s",
            group_id,
            chosen.tmdb_id,
        )


def _match_single_group_apply_persist(
    files: list[PipelineRow],
    group_key: str,
    indices: list[int],
    best: TmdbSeriesCandidate,
    confidence: float,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: _MatchPersistenceRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
    korean_status: str | None = None,
) -> None:
    del group_key
    apply_tmdb_candidate_to_file_rows(files, indices, best, korean_status=korean_status)
    if (
        root_id is None
        or not representative_path_norm
        or title_match is None
        or title_groups is None
    ):
        return
    group_id = title_groups.get_group_id_for_path_norm(root_id, representative_path_norm)
    if group_id is None:
        return
    raw_json = json.dumps(asdict(best), ensure_ascii=False, separators=(",", ":"))
    expires_at = _utc_plus_days_iso_z(TMDB_SERIES_CACHE_TTL_DAYS)
    try:
        title_match.upsert_series(best, raw_json=raw_json, expires_at=expires_at)
        existing = title_match.get_group_match(group_id)
        preserve_confirmed = (
            existing is not None
            and existing.match_status == MATCH_STATUS_CONFIRMED
            and int(existing.tmdb_id) == int(best.tmdb_id)
        )
        if not preserve_confirmed:
            title_match.set_group_match(
                group_id,
                int(best.tmdb_id),
                cast(MatchStatus, MATCH_STATUS_AUTO_MATCHED),
                confidence,
            )
    except Exception:
        logger.exception(
            "group TMDB persist failed group_id=%s tmdb_id=%s",
            group_id,
            best.tmdb_id,
        )


def apply_candidate_and_persist_for_group(
    files: list[PipelineRow],
    group_key: str,
    indices: list[int],
    candidate: TmdbSeriesCandidate,
    confidence: float,
    *,
    root_id: int | None = None,
    representative_path_norm: str | None = None,
    title_match: _MatchPersistenceRepository | None = None,
    title_groups: TitleGroupRepository | None = None,
    korean_status: str | None = None,
) -> None:
    _match_single_group_apply_persist(
        files,
        group_key,
        indices,
        candidate,
        confidence,
        root_id=root_id,
        representative_path_norm=representative_path_norm,
        title_match=title_match,
        title_groups=title_groups,
        korean_status=korean_status,
    )
