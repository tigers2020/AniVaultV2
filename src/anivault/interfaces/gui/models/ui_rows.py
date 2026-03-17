"""Presentation row types for GUI. Qt Model consumes these only."""

from dataclasses import dataclass


@dataclass
class PipelineRow:
    """One row in pipeline table. Shared by table / poster / operations."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    target_path: str
