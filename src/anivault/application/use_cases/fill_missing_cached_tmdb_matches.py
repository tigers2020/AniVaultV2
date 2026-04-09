"""Fill missing TMDB metadata/posters in background after cache hydrate."""

from __future__ import annotations

from collections.abc import Callable
from threading import Event

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.application.use_cases.match_series import (
    _index_files_by_group_key,
    _representative_path_norm_for_group,
    apply_candidate_and_persist_for_group,
    search_best_candidate_for_group,
)
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_CACHED
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.domain.rules.tmdb_image_url import tmdb_poster_cdn_url

MissingFillExecute = Callable[[MatchInput, object, Event], MatchResult]


def _try_fill_group_cached_metadata(
    files: list[MatchFileRow],
    group_key: str,
    indices: list[int],
    *,
    cancel_token: Event,
    root_id: int,
    provider: MetadataProvider,
    title_match: TitleMatchRepository,
    title_groups: TitleGroupRepository,
) -> None:
    if cancel_token.is_set():
        return
    if not _group_needs_tmdb_fill(files, indices):
        return
    path_norm = _representative_path_norm_for_group(files, root_id, indices)
    dto, candidate, provenance = search_best_candidate_for_group(
        group_key,
        provider,
        root_id=root_id,
        representative_path_norm=path_norm,
        title_match=title_match,
        title_groups=title_groups,
    )
    if candidate is None:
        return
    if not isinstance(candidate, TmdbSeriesCandidateDTO):
        return
    korean_status = PIPELINE_ROW_STATUS_TMDB_CACHED if provenance == "group_db" else None
    apply_candidate_and_persist_for_group(
        files,
        group_key,
        indices,
        candidate,
        dto.confidence,
        root_id=root_id,
        representative_path_norm=path_norm,
        title_match=title_match,
        title_groups=title_groups,
        korean_status=korean_status,
    )


def _row_eligible_for_poster_sync(row: MatchFileRow) -> bool:
    if not _has_missing_poster_data(row):
        return False
    if not (row.tmdb_series_id or "").strip():
        return False
    return bool(normalize_tmdb_remote_image_path(row.tmdb_poster_path))


def _rows_needing_poster_sync(files: list[MatchFileRow]) -> list[MatchFileRow]:
    return [row for row in files if _row_eligible_for_poster_sync(row)]


def _apply_poster_sync_if_configured(
    files: list[MatchFileRow],
    poster_sync: Callable[[MatchResult], None] | None,
    title_match: TitleMatchRepository,
) -> list[MatchFileRow]:
    if poster_sync is None:
        return files
    poster_targets = _rows_needing_poster_sync(files)
    if not poster_targets:
        return files
    poster_sync(MatchResult(files=tuple(poster_targets), groups=()))
    return _refresh_poster_display_sources(files, title_match)


def _has_missing_tmdb_metadata(row: MatchFileRow) -> bool:
    return not (row.tmdb_series_id or "").strip() or not (row.tmdb_korean_title_group or "").strip()


def _has_missing_poster_data(row: MatchFileRow) -> bool:
    return not (row.poster_url or "").strip() or not (row.tmdb_poster_path or "").strip()


def _group_needs_tmdb_fill(files: list[MatchFileRow], indices: list[int]) -> bool:
    return any(_has_missing_tmdb_metadata(files[idx]) for idx in indices)


def _refresh_poster_display_sources(
    files: list[MatchFileRow],
    title_match: TitleMatchRepository,
) -> list[MatchFileRow]:
    refreshed: list[MatchFileRow] = []
    for row in files:
        tid_s = (row.tmdb_series_id or "").strip()
        remote_path = normalize_tmdb_remote_image_path(row.tmdb_poster_path)
        if not tid_s or not remote_path:
            refreshed.append(row)
            continue
        try:
            local = title_match.get_poster_local_path(int(tid_s), "poster", remote_path)
        except (TypeError, ValueError, OSError):
            refreshed.append(row)
            continue
        remote = tmdb_poster_cdn_url(remote_path)
        display = resolve_final_poster_display_source(local, remote or row.poster_url)
        refreshed.append(
            MatchFileRow(
                original_file=row.original_file,
                parsed_title=row.parsed_title,
                parse_group=row.parse_group,
                tmdb_korean_title_group=row.tmdb_korean_title_group,
                tmdb_series_id=row.tmdb_series_id,
                tmdb_poster_path=remote_path or row.tmdb_poster_path,
                tmdb_backdrop_path=row.tmdb_backdrop_path,
                year=row.year,
                season=row.season,
                resolution=row.resolution,
                status=row.status,
                poster_url=display or row.poster_url,
                backdrop_url=row.backdrop_url,
                target_path=row.target_path,
                episode=row.episode,
            )
        )
    return refreshed


def make_execute(
    *,
    provider: MetadataProvider,
    title_match: TitleMatchRepository,
    title_groups: TitleGroupRepository,
    poster_sync: Callable[[MatchResult], None] | None = None,
) -> MissingFillExecute:
    """Create background execute that fills only missing TMDB/poster data."""

    def execute(
        input_dto: MatchInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> MatchResult:
        del progress_callback
        files = list(input_dto.files)
        if cancel_token.is_set() or not files:
            return MatchResult(files=tuple(files), groups=())
        root_id = input_dto.index_root_id
        if root_id is None:
            return MatchResult(files=tuple(files), groups=())

        key_to_indices = _index_files_by_group_key(files)
        for group_key, indices in key_to_indices.items():
            _try_fill_group_cached_metadata(
                files,
                group_key,
                indices,
                cancel_token=cancel_token,
                root_id=root_id,
                provider=provider,
                title_match=title_match,
                title_groups=title_groups,
            )

        files = _apply_poster_sync_if_configured(files, poster_sync, title_match)
        return MatchResult(files=tuple(files), groups=())

    return execute
