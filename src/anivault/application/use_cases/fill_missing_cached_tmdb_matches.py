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
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.domain.rules.tmdb_image_url import tmdb_poster_cdn_url

MissingFillExecute = Callable[[MatchInput, object, Event], MatchResult]


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
            if cancel_token.is_set() or not _group_needs_tmdb_fill(files, indices):
                continue
            path_norm = _representative_path_norm_for_group(files, root_id, indices)
            dto, candidate = search_best_candidate_for_group(
                group_key,
                provider,
                root_id=root_id,
                representative_path_norm=path_norm,
                title_match=title_match,
                title_groups=title_groups,
            )
            if candidate is None or not isinstance(candidate, TmdbSeriesCandidateDTO):
                continue
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
            )

        if poster_sync is not None:
            poster_targets = [
                row
                for row in files
                if _has_missing_poster_data(row)
                and (row.tmdb_series_id or "").strip()
                and normalize_tmdb_remote_image_path(row.tmdb_poster_path)
            ]
            if poster_targets:
                poster_sync(MatchResult(files=tuple(poster_targets), groups=()))
                files = _refresh_poster_display_sources(files, title_match)

        return MatchResult(files=tuple(files), groups=())

    return execute
