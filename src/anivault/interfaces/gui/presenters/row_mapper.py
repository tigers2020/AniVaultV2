"""Shared row mappers for organizer presenter/coordinators."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from anivault.application.ports.title_match_port import PosterAssetRepository
from anivault.constants.gui.components import SCAN_PARSE_COORDINATOR_STATUS_SCANNED
from anivault.contracts.pipeline import PipelineRow
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path


def pipeline_row_to_match_file(row: PipelineRow) -> PipelineRow:
    """Return the shared pipeline row for use-case inputs."""

    return row


def match_file_to_pipeline_row(
    match_file: PipelineRow,
    *,
    title_match: PosterAssetRepository | None = None,
) -> PipelineRow:
    """Normalize poster display state for a shared pipeline row."""

    local_poster: str | None = None
    if title_match is not None:
        tmdb_series_id = (match_file.tmdb_series_id or "").strip()
        remote_poster_path = normalize_tmdb_remote_image_path(match_file.tmdb_poster_path)
        if tmdb_series_id and remote_poster_path:
            try:
                local_poster = title_match.get_poster_local_path(
                    int(tmdb_series_id),
                    "poster",
                    remote_poster_path,
                )
            except (OSError, TypeError, ValueError):
                local_poster = None
    poster_display = resolve_final_poster_display_source(local_poster, match_file.poster_url)
    if poster_display == match_file.poster_url:
        return match_file
    return replace(match_file, poster_url=poster_display)


def scan_path_to_pipeline_row(path: str, resolution: str) -> PipelineRow:
    """Create the initial pipeline row produced by scan results."""

    return PipelineRow(
        original_file=path,
        parsed_title="",
        parse_group="",
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="",
        resolution=resolution,
        status=SCAN_PARSE_COORDINATOR_STATUS_SCANNED,
        poster_url="",
        backdrop_url="",
        target_path="",
        episode="",
    )


def copy_pipeline_row(row: PipelineRow, **changes: str | None) -> PipelineRow:
    """Return a copy-like PipelineRow with selected fields replaced."""

    allowed_fields = frozenset(
        {
            "parsed_title",
            "parse_group",
            "tmdb_korean_title_group",
            "tmdb_series_id",
            "tmdb_poster_path",
            "tmdb_backdrop_path",
            "year",
            "season",
            "resolution",
            "status",
            "poster_url",
            "backdrop_url",
            "target_path",
            "episode",
        }
    )
    invalid_fields = tuple(sorted(set(changes) - allowed_fields))
    if invalid_fields:
        invalid = ", ".join(invalid_fields)
        raise TypeError(f"Unexpected field(s) for copy_pipeline_row: {invalid}")
    updates = {field_name: value for field_name, value in changes.items() if value is not None}
    if not updates:
        return row
    return replace(row, **updates)


def pipeline_rows_to_match_files(rows: Iterable[PipelineRow]) -> tuple[PipelineRow, ...]:
    """Return shared pipeline rows as a tuple for use-case inputs."""

    return tuple(rows)
