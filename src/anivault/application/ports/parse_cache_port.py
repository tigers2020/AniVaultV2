"""Port for parse cache persistence."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from anivault.contracts.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.domain.models import ParsedInfo


@runtime_checkable
class ParseCacheRepository(Protocol):
    def get_valid_parse(self, media_file_id: int, signature: str) -> ParsedInfo | None: ...

    def get_valid_parses(self, lookups: list[ParseCacheLookup]) -> dict[int, ParsedInfo]: ...

    def upsert_parse_ok(
        self,
        *,
        media_file_id: int,
        parser_version: str,
        parse_input_signature: str,
        parsed: ParsedInfo,
        dto_json: str,
        parsed_title: str | None,
        parsed_title_normalized: str | None,
        parsed_year: int | None,
        season_number: int | None,
        episode_start: int | None,
        episode_end: int | None,
        episode_count: int | None,
        confidence: float | None,
    ) -> None: ...

    def upsert_parse_ok_many(self, items: list[ParseCacheOkWrite]) -> None: ...

    def upsert_parse_error(
        self,
        *,
        media_file_id: int,
        parser_version: str,
        parse_input_signature: str,
        error_code: str | None,
        error_message: str | None,
    ) -> None: ...

    def upsert_parse_error_many(self, items: list[ParseCacheErrorWrite]) -> None: ...

    def resolution_write_batch(self) -> AbstractContextManager[None]: ...

    def get_valid_resolution(self, media_file_id: int, signature: str) -> str | None: ...

    def upsert_resolution(
        self,
        *,
        media_file_id: int,
        signature: str,
        value: str,
        source: str,
    ) -> None: ...
