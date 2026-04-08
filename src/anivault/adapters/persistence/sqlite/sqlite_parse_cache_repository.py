"""SQLite implementation of the parse cache repository."""

from __future__ import annotations

import logging
import sqlite3
from threading import Lock
from typing import Any

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.parse import ParsedInfo
from anivault.application.dto.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.application.dto.parse_serde import parsed_info_from_compact_json

logger = logging.getLogger(__name__)

_ERROR_DTO_JSON = "{}"
_LOOKUP_CHUNK = 500

_PARSE_OK_UPSERT_SQL = """
INSERT INTO parse_cache (
    media_file_id, parser_version, parse_status, parse_input_signature,
    parsed_title, parsed_title_normalized, parsed_year, season_number,
    episode_start, episode_end, episode_count, confidence,
    dto_json, error_code, error_message, created_at, updated_at
) VALUES (?, ?, 'ok', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
ON CONFLICT(media_file_id) DO UPDATE SET
    parser_version = excluded.parser_version,
    parse_status = excluded.parse_status,
    parse_input_signature = excluded.parse_input_signature,
    parsed_title = excluded.parsed_title,
    parsed_title_normalized = excluded.parsed_title_normalized,
    parsed_year = excluded.parsed_year,
    season_number = excluded.season_number,
    episode_start = excluded.episode_start,
    episode_end = excluded.episode_end,
    episode_count = excluded.episode_count,
    confidence = excluded.confidence,
    dto_json = excluded.dto_json,
    error_code = NULL,
    error_message = NULL,
    updated_at = excluded.updated_at
"""

_PARSE_ERROR_UPSERT_SQL = """
INSERT INTO parse_cache (
    media_file_id, parser_version, parse_status, parse_input_signature,
    parsed_title, parsed_title_normalized, parsed_year, season_number,
    episode_start, episode_end, episode_count, confidence,
    dto_json, error_code, error_message, created_at, updated_at
) VALUES (
    ?, ?, 'error', ?,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    ?, ?, ?, ?, ?
)
ON CONFLICT(media_file_id) DO UPDATE SET
    parser_version = excluded.parser_version,
    parse_status = excluded.parse_status,
    parse_input_signature = excluded.parse_input_signature,
    parsed_title = NULL,
    parsed_title_normalized = NULL,
    parsed_year = NULL,
    season_number = NULL,
    episode_start = NULL,
    episode_end = NULL,
    episode_count = NULL,
    confidence = NULL,
    dto_json = excluded.dto_json,
    error_code = excluded.error_code,
    error_message = excluded.error_message,
    updated_at = excluded.updated_at
"""


class SqliteParseCacheRepository:
    """Access parse_cache rows."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        self._conn = conn
        self._lock = lock

    def get_valid_parse(self, media_file_id: int, signature: str) -> ParsedInfo | None:
        """Return one valid cache hit, or None."""
        return self.get_valid_parses([ParseCacheLookup(media_file_id, signature)]).get(
            media_file_id
        )

    def get_valid_parses(self, lookups: list[ParseCacheLookup]) -> dict[int, ParsedInfo]:
        """Bulk read valid cache hits keyed by media_file_id."""
        if not lookups:
            return {}
        signature_by_id: dict[int, str] = {}
        media_ids: list[int] = []
        for lookup in lookups:
            if lookup.media_file_id not in signature_by_id:
                signature_by_id[lookup.media_file_id] = lookup.signature
                media_ids.append(lookup.media_file_id)

        rows: list[tuple[Any, ...]] = []
        with self._lock:
            for start in range(0, len(media_ids), _LOOKUP_CHUNK):
                chunk = media_ids[start : start + _LOOKUP_CHUNK]
                placeholders = ",".join("?" * len(chunk))
                cur = self._conn.execute(
                    f"""
                    SELECT media_file_id, parse_status, parse_input_signature, dto_json
                    FROM parse_cache
                    WHERE media_file_id IN ({placeholders})
                    """,
                    chunk,
                )
                rows.extend(cur.fetchall())

        out: dict[int, ParsedInfo] = {}
        for row in rows:
            media_file_id = int(row[0])
            status = str(row[1])
            stored_sig = str(row[2])
            dto_json = str(row[3])
            if status != "ok" or stored_sig != signature_by_id.get(media_file_id):
                continue
            try:
                out[media_file_id] = parsed_info_from_compact_json(dto_json)
            except (OSError, TypeError, ValueError) as e:
                logger.warning(
                    "parse_cache dto_json deserialize failed media_file_id=%s: %s",
                    media_file_id,
                    e,
                )
        return out

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
    ) -> None:
        """Upsert one successful parse row."""
        self.upsert_parse_ok_many(
            [
                ParseCacheOkWrite(
                    media_file_id=media_file_id,
                    parser_version=parser_version,
                    parse_input_signature=parse_input_signature,
                    parsed=parsed,
                    dto_json=dto_json,
                    parsed_title=parsed_title,
                    parsed_title_normalized=parsed_title_normalized,
                    parsed_year=parsed_year,
                    season_number=season_number,
                    episode_start=episode_start,
                    episode_end=episode_end,
                    episode_count=episode_count,
                    confidence=confidence,
                )
            ]
        )

    def upsert_parse_ok_many(self, items: list[ParseCacheOkWrite]) -> None:
        """Bulk upsert successful parse rows in one transaction."""
        if not items:
            return
        for item in items:
            assert isinstance(item.parsed, ParsedInfo)
        now = utc_now_sqlite_text()
        params = [
            (
                item.media_file_id,
                item.parser_version,
                item.parse_input_signature,
                item.parsed_title,
                item.parsed_title_normalized,
                item.parsed_year,
                item.season_number,
                item.episode_start,
                item.episode_end,
                item.episode_count,
                item.confidence,
                item.dto_json,
                now,
                now,
            )
            for item in items
        ]
        with self._lock:
            try:
                self._conn.executemany(_PARSE_OK_UPSERT_SQL, params)
                self._conn.commit()
            except sqlite3.Error as e:
                self._conn.rollback()
                logger.exception(
                    "parse_cache upsert_parse_ok_many failed count=%s: %s",
                    len(items),
                    e,
                )

    def upsert_parse_error(
        self,
        *,
        media_file_id: int,
        parser_version: str,
        parse_input_signature: str,
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        """Upsert one parse error row."""
        self.upsert_parse_error_many(
            [
                ParseCacheErrorWrite(
                    media_file_id=media_file_id,
                    parser_version=parser_version,
                    parse_input_signature=parse_input_signature,
                    error_code=error_code,
                    error_message=error_message,
                )
            ]
        )

    def upsert_parse_error_many(self, items: list[ParseCacheErrorWrite]) -> None:
        """Bulk upsert parse error rows in one transaction."""
        if not items:
            return
        now = utc_now_sqlite_text()
        params = [
            (
                item.media_file_id,
                item.parser_version,
                item.parse_input_signature,
                _ERROR_DTO_JSON,
                item.error_code,
                item.error_message,
                now,
                now,
            )
            for item in items
        ]
        with self._lock:
            try:
                self._conn.executemany(_PARSE_ERROR_UPSERT_SQL, params)
                self._conn.commit()
            except sqlite3.Error as e:
                self._conn.rollback()
                logger.exception(
                    "parse_cache upsert_parse_error_many failed count=%s: %s",
                    len(items),
                    e,
                )
