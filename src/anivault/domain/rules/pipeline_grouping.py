"""Shared grouping rules for pipeline rows."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class GroupablePipelineRow(Protocol):
    @property
    def original_file(self) -> str: ...

    @property
    def parsed_title(self) -> str: ...

    @property
    def tmdb_korean_title_group(self) -> str: ...

    @property
    def tmdb_series_id(self) -> str: ...


def pipeline_row_group_key(row: GroupablePipelineRow) -> str:
    """Return the canonical grouping key for a pipeline row."""

    tmdb_series_id = (row.tmdb_series_id or "").strip()
    if tmdb_series_id:
        return f"tmdb:{tmdb_series_id}"
    parsed_title = (row.parsed_title or "").strip()
    if parsed_title:
        return parsed_title
    return row.original_file


def pipeline_row_group_label(row: GroupablePipelineRow) -> str:
    """Return the user-facing label for a pipeline row group."""

    group_title = (row.tmdb_korean_title_group or "").strip()
    if group_title:
        return group_title
    parsed_title = (row.parsed_title or "").strip()
    if parsed_title:
        return parsed_title
    return Path(row.original_file).name
