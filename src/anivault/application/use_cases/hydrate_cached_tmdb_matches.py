"""Hydrate TMDB match fields from the local SQLite cache only."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.constants.application.statuses import (
    MATCH_STATUS_AUTO_MATCHED,
    MATCH_STATUS_CONFIRMED,
    POSTER_ASSET_KIND_POSTER,
)
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_CACHED
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.domain.rules.tmdb_image_url import tmdb_backdrop_cdn_url, tmdb_poster_cdn_url


def _group_key(row: MatchFileRow) -> str:
    pg = (row.parse_group or "").strip()
    if pg:
        return pg
    pt = (row.parsed_title or "").strip()
    if pt:
        return pt
    return row.original_file


def _year_prefix(iso_date: str) -> str:
    d = (iso_date or "").strip()
    return d[:4] if len(d) >= 4 else ""


def _lexical_path_key(path: str) -> str:
    p = Path(path).expanduser()
    s = p.as_posix()
    if len(s) > 1 and s.endswith("/"):
        s = s.rstrip("/")
        if s.endswith(":"):
            s = s + "/"
    if os.name == "nt" or sys.platform.startswith("win"):
        return os.path.normcase(s)
    return s


def _apply_cached_candidate(
    row: MatchFileRow,
    candidate: TmdbSeriesCandidateDTO,
    poster_local_path_for: Callable[[int, str, str], str | None],
) -> MatchFileRow:
    poster_remote = normalize_tmdb_remote_image_path(candidate.poster_path)
    backdrop_remote = normalize_tmdb_remote_image_path(candidate.backdrop_path)
    poster_cdn = tmdb_poster_cdn_url(poster_remote)
    backdrop_cdn = tmdb_backdrop_cdn_url(backdrop_remote)
    local_poster: str | None = None
    if candidate.tmdb_id and poster_remote:
        local_poster = poster_local_path_for(
            int(candidate.tmdb_id),
            POSTER_ASSET_KIND_POSTER,
            poster_remote,
        )
    poster_display = resolve_final_poster_display_source(local_poster, poster_cdn)
    year = _year_prefix(candidate.first_air_date)
    return MatchFileRow(
        original_file=row.original_file,
        parsed_title=row.parsed_title,
        parse_group=row.parse_group,
        tmdb_korean_title_group=(candidate.name_ko or "").strip() or row.tmdb_korean_title_group,
        tmdb_series_id=str(candidate.tmdb_id),
        tmdb_poster_path=poster_remote or row.tmdb_poster_path,
        tmdb_backdrop_path=backdrop_remote or row.tmdb_backdrop_path,
        year=year or row.year,
        season=row.season,
        resolution=row.resolution,
        status=PIPELINE_ROW_STATUS_TMDB_CACHED if (candidate.name_ko or "").strip() else row.status,
        poster_url=poster_display or row.poster_url,
        backdrop_url=backdrop_cdn or row.backdrop_url,
        target_path=row.target_path,
        episode=row.episode,
    )


def _collect_group_paths(files: list[MatchFileRow]) -> tuple[
    dict[str, list[str]],
    dict[str, list[str]],
    list[str],
]:
    paths_by_current_group: dict[str, list[str]] = {}
    lexical_norms_by_current_group: dict[str, list[str]] = {}
    all_lexical_norms: list[str] = []
    for row in files:
        current_group_key = _group_key(row)
        paths_by_current_group.setdefault(current_group_key, []).append(row.original_file)
        path_norm = _lexical_path_key(row.original_file)
        lexical_norms_by_current_group.setdefault(current_group_key, []).append(path_norm)
        all_lexical_norms.append(path_norm)
    return paths_by_current_group, lexical_norms_by_current_group, all_lexical_norms


def _resolve_group_ids_from_norms(
    lexical_norms_by_current_group: dict[str, list[str]],
    group_id_by_path_norm: dict[str, int],
) -> tuple[dict[str, int], list[str]]:
    group_id_by_current_group: dict[str, int] = {}
    missing_current_groups: list[str] = []
    for current_group_key, path_norms in lexical_norms_by_current_group.items():
        for path_norm in path_norms:
            group_id = group_id_by_path_norm.get(path_norm)
            if group_id is not None:
                group_id_by_current_group[current_group_key] = group_id
                break
        else:
            missing_current_groups.append(current_group_key)
    return group_id_by_current_group, missing_current_groups


def _apply_fallback_group_ids(
    *,
    root_id: int,
    title_groups: TitleGroupRepository,
    paths_by_current_group: dict[str, list[str]],
    missing_current_groups: list[str],
    group_id_by_current_group: dict[str, int],
) -> None:
    if not missing_current_groups:
        return

    fallback_norms_by_current_group: dict[str, list[str]] = {}
    all_fallback_norms: list[str] = []
    for current_group_key in missing_current_groups:
        for original_file in paths_by_current_group[current_group_key]:
            try:
                path_norm = normalize_path_key(original_file)
            except OSError:
                continue
            fallback_norms_by_current_group.setdefault(current_group_key, []).append(path_norm)
            all_fallback_norms.append(path_norm)

    fallback_group_id_by_path_norm = title_groups.get_group_ids_for_path_norms(
        root_id,
        all_fallback_norms,
    )
    for current_group_key, path_norms in fallback_norms_by_current_group.items():
        for path_norm in path_norms:
            group_id = fallback_group_id_by_path_norm.get(path_norm)
            if group_id is not None:
                group_id_by_current_group[current_group_key] = group_id
                break


def _candidate_by_current_group(
    *,
    title_match: TitleMatchRepository,
    group_id_by_current_group: dict[str, int],
) -> dict[str, TmdbSeriesCandidateDTO]:
    matches_by_group_id = title_match.get_group_matches(
        list(group_id_by_current_group.values()),
    )
    tmdb_ids = [
        match.tmdb_id
        for match in matches_by_group_id.values()
        if match.match_status in (MATCH_STATUS_AUTO_MATCHED, MATCH_STATUS_CONFIRMED)
    ]
    candidates_by_tmdb_id = title_match.get_series_candidates(tmdb_ids)
    result: dict[str, TmdbSeriesCandidateDTO] = {}
    for current_group_key, group_id in group_id_by_current_group.items():
        match = matches_by_group_id.get(group_id)
        if match is None or match.match_status not in (
            MATCH_STATUS_AUTO_MATCHED,
            MATCH_STATUS_CONFIRMED,
        ):
            continue
        candidate = candidates_by_tmdb_id.get(match.tmdb_id)
        if candidate is None:
            continue
        result[current_group_key] = candidate
    return result


def _build_poster_local_path_getter(
    title_match: TitleMatchRepository,
) -> Callable[[int, str, str], str | None]:
    poster_local_path_cache: dict[tuple[int, str, str], str | None] = {}

    def poster_local_path_for(
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
    ) -> str | None:
        key = (tmdb_id, image_kind, remote_path)
        if key not in poster_local_path_cache:
            poster_local_path_cache[key] = title_match.get_poster_local_path(
                tmdb_id,
                image_kind,
                remote_path,
            )
        return poster_local_path_cache[key]

    return poster_local_path_for


def _hydrate_rows(
    files: list[MatchFileRow],
    candidate_by_current_group: dict[str, TmdbSeriesCandidateDTO],
    poster_local_path_for: Callable[[int, str, str], str | None],
) -> list[MatchFileRow]:
    hydrated: list[MatchFileRow] = []
    for row in files:
        current_group_key = _group_key(row)
        candidate = candidate_by_current_group.get(current_group_key)
        if candidate is None:
            hydrated.append(row)
            continue
        hydrated.append(_apply_cached_candidate(row, candidate, poster_local_path_for))
    return hydrated


def make_execute(
    *,
    title_match: TitleMatchRepository,
    title_groups: TitleGroupRepository,
) -> Callable[[MatchInput], MatchResult]:
    """Create a cache-only TMDB hydration function.

    This function never calls a metadata provider or the network. It only reads
    title_groups, group_tmdb_matches, tmdb_series, and poster_assets.
    """

    def execute(input_dto: MatchInput) -> MatchResult:
        root_id = input_dto.index_root_id
        files = list(input_dto.files)
        if root_id is None or not files:
            return MatchResult(files=tuple(files), groups=())

        (
            paths_by_current_group,
            lexical_norms_by_current_group,
            all_lexical_norms,
        ) = _collect_group_paths(files)

        group_id_by_path_norm = title_groups.get_group_ids_for_path_norms(
            root_id,
            all_lexical_norms,
        )
        group_id_by_current_group, missing_current_groups = _resolve_group_ids_from_norms(
            lexical_norms_by_current_group,
            group_id_by_path_norm,
        )
        _apply_fallback_group_ids(
            root_id=root_id,
            title_groups=title_groups,
            paths_by_current_group=paths_by_current_group,
            missing_current_groups=missing_current_groups,
            group_id_by_current_group=group_id_by_current_group,
        )

        candidate_by_current_group = _candidate_by_current_group(
            title_match=title_match,
            group_id_by_current_group=group_id_by_current_group,
        )
        poster_local_path_for = _build_poster_local_path_getter(title_match)
        hydrated = _hydrate_rows(
            files,
            candidate_by_current_group,
            poster_local_path_for,
        )
        return MatchResult(files=tuple(hydrated), groups=())

    return execute
