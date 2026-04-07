"""Hydrate TMDB match fields from the local SQLite cache only."""

from __future__ import annotations

from collections.abc import Callable

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


def _apply_cached_candidate(
    row: MatchFileRow,
    candidate: TmdbSeriesCandidateDTO,
    title_match: TitleMatchRepository,
) -> MatchFileRow:
    poster_remote = normalize_tmdb_remote_image_path(candidate.poster_path)
    backdrop_remote = normalize_tmdb_remote_image_path(candidate.backdrop_path)
    poster_cdn = tmdb_poster_cdn_url(poster_remote)
    backdrop_cdn = tmdb_backdrop_cdn_url(backdrop_remote)
    local_poster: str | None = None
    if candidate.tmdb_id and poster_remote:
        local_poster = title_match.get_poster_local_path(
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

        candidate_by_group_id: dict[int, TmdbSeriesCandidateDTO | None] = {}
        candidate_by_current_group: dict[str, TmdbSeriesCandidateDTO] = {}
        for row in files:
            current_group_key = _group_key(row)
            if current_group_key in candidate_by_current_group:
                continue
            try:
                path_norm = normalize_path_key(row.original_file)
            except OSError:
                continue
            group_id = title_groups.get_group_id_for_path_norm(root_id, path_norm)
            if group_id is None:
                continue
            if group_id not in candidate_by_group_id:
                match = title_match.get_group_match(group_id)
                candidate_by_group_id[group_id] = (
                    title_match.get_series_candidate(match.tmdb_id)
                    if match is not None and match.match_status in ("auto_matched", "confirmed")
                    else None
                )
            candidate = candidate_by_group_id[group_id]
            if candidate is None:
                continue
            candidate_by_current_group[current_group_key] = candidate
        hydrated = [
            (
                _apply_cached_candidate(
                    row, candidate_by_current_group[_group_key(row)], title_match
                )
                if _group_key(row) in candidate_by_current_group
                else row
            )
            for row in files
        ]
        return MatchResult(files=tuple(hydrated), groups=())

    return execute
