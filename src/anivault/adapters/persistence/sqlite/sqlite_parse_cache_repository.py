"""sqlite_parse_cache_repository.py

ParseCacheRepository SQLite 구현. updated_at·created_at은 메서드에서 수동 설정.

Author: Pom Kim
"""

from __future__ import annotations

import logging
import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.parse import ParsedInfo
from anivault.application.dto.parse_serde import parsed_info_from_compact_json

logger = logging.getLogger(__name__)

_ERROR_DTO_JSON = "{}"

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

_RESOLUTION_CACHE_UPSERT_SQL = """
INSERT INTO parse_cache (
    media_file_id,
    parser_version,
    parse_status,
    parse_input_signature,
    dto_json,
    resolution_value,
    resolution_source,
    resolution_signature,
    created_at,
    updated_at
) VALUES (?, 'resolution-only', 'error', '', '{}', ?, ?, ?, ?, ?)
ON CONFLICT(media_file_id) DO UPDATE SET
    resolution_value = excluded.resolution_value,
    resolution_source = excluded.resolution_source,
    resolution_signature = excluded.resolution_signature,
    updated_at = excluded.updated_at
"""


class SqliteParseCacheRepository:
    """parse_cache 테이블 접근."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 직렬화 Lock을 받는다.

        Args:
            self: 저장소.
            conn: 공유 SQLite 연결.
            lock: 메서드 단위 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def get_valid_parse(self, media_file_id: int, signature: str) -> ParsedInfo | None:
        """ok·서명·JSON이 유효할 때만 ParsedInfo를 반환한다.

        Args:
            self: 저장소.
            media_file_id: 미디어 행 ID.
            signature: 입력 서명.

        Returns:
            캐시 hit 시 ParsedInfo. miss면 None.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT parse_status, parse_input_signature, dto_json
                FROM parse_cache
                WHERE media_file_id = ?
                """,
                (media_file_id,),
            )
            row = cur.fetchone()
            self._conn.commit()
        if row is None:
            return None
        status, stored_sig, dto_json = str(row[0]), str(row[1]), str(row[2])
        if status != "ok":
            return None
        if stored_sig != signature:
            return None
        try:
            return parsed_info_from_compact_json(dto_json)
        except (OSError, TypeError, ValueError) as e:
            logger.warning(
                "parse_cache dto_json 역직렬화 실패 media_file_id=%s: %s",
                media_file_id,
                e,
            )
            return None

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
        """성공 행을 upsert한다.

        Args:
            self: 저장소.
            media_file_id: 미디어 행 ID.
            parser_version: 기록용 버전 문자열.
            parse_input_signature: 서명.
            parsed: 참고용 ParsedInfo.
            dto_json: compact JSON.
            parsed_title: 정규 컬럼.
            parsed_title_normalized: 정규화 제목.
            parsed_year: 연도.
            season_number: 시즌.
            episode_start: 에피소드 시작.
            episode_end: 에피소드 끝.
            episode_count: 에피소드 수.
            confidence: 신뢰도.

        Returns:
            None.
        """
        assert isinstance(parsed, ParsedInfo)
        now = utc_now_sqlite_text()
        with self._lock:
            try:
                self._conn.execute(
                    _PARSE_OK_UPSERT_SQL,
                    (
                        media_file_id,
                        parser_version,
                        parse_input_signature,
                        parsed_title,
                        parsed_title_normalized,
                        parsed_year,
                        season_number,
                        episode_start,
                        episode_end,
                        episode_count,
                        confidence,
                        dto_json,
                        now,
                        now,
                    ),
                )
                self._conn.commit()
            except sqlite3.Error as e:
                self._conn.rollback()
                logger.exception(
                    "parse_cache upsert_parse_ok 실패 media_file_id=%s: %s", media_file_id, e
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
        """에러 행을 upsert한다(dto_json은 `{}`).

        Args:
            self: 저장소.
            media_file_id: 미디어 행 ID.
            parser_version: 기록용.
            parse_input_signature: 서명.
            error_code: 코드.
            error_message: 메시지.

        Returns:
            None.
        """
        now = utc_now_sqlite_text()
        with self._lock:
            try:
                self._conn.execute(
                    _PARSE_ERROR_UPSERT_SQL,
                    (
                        media_file_id,
                        parser_version,
                        parse_input_signature,
                        _ERROR_DTO_JSON,
                        error_code,
                        error_message,
                        now,
                        now,
                    ),
                )
                self._conn.commit()
            except sqlite3.Error as e:
                self._conn.rollback()
                logger.exception(
                    "parse_cache upsert_parse_error 실패 media_file_id=%s: %s",
                    media_file_id,
                    e,
                )

    def get_valid_resolution(self, media_file_id: int, signature: str) -> str | None:
        """서명이 일치하는 해상도 캐시를 반환한다.

        Args:
            self: 저장소.
            media_file_id: 미디어 행 ID.
            signature: 해상도 캐시 무효화 서명.

        Returns:
            해상도 문자열. miss면 None.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT resolution_value, resolution_signature
                FROM parse_cache
                WHERE media_file_id = ?
                """,
                (media_file_id,),
            )
            row = cur.fetchone()
            self._conn.commit()
        if row is None:
            return None
        value = row[0]
        stored_sig = row[1]
        if not isinstance(value, str) or not value.strip():
            return None
        if not isinstance(stored_sig, str) or stored_sig != signature:
            return None
        return value.strip()

    def upsert_resolution(
        self,
        *,
        media_file_id: int,
        signature: str,
        value: str,
        source: str,
    ) -> None:
        """해상도 캐시를 upsert한다.

        Args:
            self: 저장소.
            media_file_id: 미디어 행 ID.
            signature: 해상도 캐시 무효화 서명.
            value: 저장할 해상도 값.
            source: 값 출처.

        Returns:
            None.
        """
        normalized = (value or "").strip()
        if not normalized:
            return
        now = utc_now_sqlite_text()
        with self._lock:
            try:
                self._conn.execute(
                    _RESOLUTION_CACHE_UPSERT_SQL,
                    (
                        media_file_id,
                        normalized,
                        (source or "").strip() or "unknown",
                        signature,
                        now,
                        now,
                    ),
                )
                self._conn.commit()
            except sqlite3.Error as e:
                self._conn.rollback()
                logger.exception(
                    "parse_cache upsert_resolution 실패 media_file_id=%s: %s",
                    media_file_id,
                    e,
                )
