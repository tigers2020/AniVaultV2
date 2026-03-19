"""DTOs for parse_titles use case."""

from dataclasses import dataclass, field


@dataclass
class ParsedInfo:
    """경량 파싱 결과. title, parse_group, year, season, resolution."""

    title: str = ""
    parse_group: str = ""
    year: str = ""
    season: str = ""
    resolution: str = ""


@dataclass
class ParseInput:
    """Input for parse_titles use case. Paths in pipeline order."""

    paths: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Result from parse_titles. ParsedInfo per path, same order as ParseInput.paths."""

    parsed: list[ParsedInfo] = field(default_factory=list)
