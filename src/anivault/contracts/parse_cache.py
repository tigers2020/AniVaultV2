"""Parse cache contracts."""

from __future__ import annotations

from dataclasses import dataclass

from anivault.domain.models import ParsedInfo


@dataclass(frozen=True, slots=True)
class ParseCacheLookup:
    media_file_id: int
    signature: str


@dataclass(frozen=True, slots=True)
class ParseCacheOkWrite:
    media_file_id: int
    parser_version: str
    parse_input_signature: str
    parsed: ParsedInfo
    dto_json: str
    parsed_title: str | None
    parsed_title_normalized: str | None
    parsed_year: int | None
    season_number: int | None
    episode_start: int | None
    episode_end: int | None
    episode_count: int | None
    confidence: float | None


@dataclass(frozen=True, slots=True)
class ParseCacheErrorWrite:
    media_file_id: int
    parser_version: str
    parse_input_signature: str
    error_code: str | None
    error_message: str | None
