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
            "poster",
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
        status="TMDB cached" if (candidate.name_ko or "").strip() else row.status,
        poster_url=poster_display or row.poster_url,
        backdrop_url=backdrop_cdn or row.backdrop_url,
        target_path=row.target_path,
        episode=row.episode,
    )


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

        paths_by_current_group: dict[str, list[str]] = {}
        lexical_norms_by_current_group: dict[str, list[str]] = {}
        all_lexical_norms: list[str] = []
        for row in files:
            current_group_key = _group_key(row)
            paths_by_current_group.setdefault(current_group_key, []).append(row.original_file)
            path_norm = _lexical_path_key(row.original_file)
            lexical_norms_by_current_group.setdefault(current_group_key, []).append(path_norm)
            all_lexical_norms.append(path_norm)

        group_id_by_path_norm = title_groups.get_group_ids_for_path_norms(
            root_id,
            all_lexical_norms,
        )
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

        if missing_current_groups:
            fallback_norms_by_current_group: dict[str, list[str]] = {}
            all_fallback_norms: list[str] = []
            for current_group_key in missing_current_groups:
                for original_file in paths_by_current_group[current_group_key]:
                    try:
                        path_norm = normalize_path_key(original_file)
                    except OSError:
                        continue
                    fallback_norms_by_current_group.setdefault(current_group_key, []).append(
                        path_norm,
                    )
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

        matches_by_group_id = title_match.get_group_matches(
            list(group_id_by_current_group.values()),
        )
        tmdb_ids = [
            match.tmdb_id
            for match in matches_by_group_id.values()
            if match.match_status in ("auto_matched", "confirmed")
        ]
        candidates_by_tmdb_id = title_match.get_series_candidates(tmdb_ids)
        candidate_by_current_group: dict[str, TmdbSeriesCandidateDTO] = {}
        for current_group_key, group_id in group_id_by_current_group.items():
            match = matches_by_group_id.get(group_id)
            if match is None or match.match_status not in ("auto_matched", "confirmed"):
                continue
            candidate = candidates_by_tmdb_id.get(match.tmdb_id)
            if candidate is None:
                continue
            candidate_by_current_group[current_group_key] = candidate

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

        hydrated = [
            (
                _apply_cached_candidate(
                    row,
                    candidate_by_current_group[_group_key(row)],
                    poster_local_path_for,
                )
                if _group_key(row) in candidate_by_current_group
                else row
            )
            for row in files
        ]
        return MatchResult(files=tuple(hydrated), groups=())

    return execute
