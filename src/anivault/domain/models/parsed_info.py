"""Parsed title information used by domain parsing rules."""

from dataclasses import dataclass


@dataclass
class ParsedInfo:
    """Lightweight parsing result shared by domain rules and application DTOs."""

    title: str = ""
    parse_group: str = ""
    year: str = ""
    season: str = ""
    episode: str = ""
    resolution: str = ""
