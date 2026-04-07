"""parse.py

parse_titles 유스케이스용 DTO: ParsedInfo, ParseInput, ParseResult.

Author: Pom Kim
"""

from dataclasses import dataclass, field

from anivault.domain.models.parsed_info import ParsedInfo


@dataclass
class ParseInput:
    """parse_titles 입력. 경로는 파이프라인 순서."""

    paths: list[str] = field(default_factory=list)
    index_root_id: int | None = None


@dataclass
class ParseResult:
    """parse_titles 결과. ParsedInfo는 ParseInput.paths와 동일 순서."""

    parsed: list[ParsedInfo] = field(default_factory=list)
    cache_hits: list[bool] = field(default_factory=list)


__all__ = ["ParsedInfo", "ParseInput", "ParseResult"]
