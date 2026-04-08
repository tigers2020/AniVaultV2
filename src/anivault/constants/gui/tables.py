"""GUI table metadata constants."""

from __future__ import annotations

from typing import Final

PIPELINE_TABLE_COLUMNS: Final[list[tuple[str, str]]] = [
    ("Original File", "original_file"),
    ("Parsed Title", "parsed_title"),
    ("Parse Title Group", "parse_group"),
    ("TMDB Korean Title Group", "tmdb_korean_title_group"),
    ("Year", "year"),
    ("Season", "season"),
    ("Ep", "episode"),
    ("Res", "resolution"),
    ("Status", "status"),
]
