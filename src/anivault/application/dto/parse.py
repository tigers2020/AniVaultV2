"""parse.py

parse_titles 유스케이스용 DTO: ParsedInfo, ParseInput, ParseResult.

Author: Pom Kim
"""

from dataclasses import dataclass, field


@dataclass
class ParsedInfo:
    """경량 파싱 결과. title, parse_group, year, season, episode, resolution."""

    title: str = ""
    parse_group: str = ""
    year: str = ""
    season: str = ""
    episode: str = ""
    resolution: str = ""


@dataclass
class ParseInput:
    """parse_titles 입력. 경로는 파이프라인 순서."""

    paths: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """parse_titles 결과. ParsedInfo는 ParseInput.paths와 동일 순서."""

    parsed: list[ParsedInfo] = field(default_factory=list)
