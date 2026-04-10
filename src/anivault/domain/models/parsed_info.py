"""Parsed title information used by domain parsing rules."""

from dataclasses import dataclass, field


@dataclass
class ParsedInfo:
    """Lightweight parsing result shared by domain rules and application DTOs."""

    title: str = ""
    parse_group: str = ""
    year: str = ""
    season: str = ""
    episode: str = ""
    episode_numbers: list[int] = field(default_factory=list)
    resolution: str = ""
