"""parse_cache_port.py

파싱 결과 SQLite 캐시 포트. 유스케이스는 Protocol만 의존한다.

Author: Pom Kim
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable

from anivault.application.dto.parse import ParsedInfo
from anivault.application.dto.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)


@runtime_checkable
class ParseCacheRepository(Protocol):
    """파일당 최신 파싱 캐시. `get_valid_parse`는 `ok`+서명+JSON만 hit."""

    def get_valid_parse(self, media_file_id: int, signature: str) -> ParsedInfo | None:
        """서명이 맞고 `ok`이며 JSON 역직렬화 성공일 때만 ParsedInfo를 반환한다.

        Args:
            self: 저장소.
            media_file_id: `media_files.id`.
            signature: `compute_parse_input_signature` 결과.

        Returns:
            캐시된 최종 ParsedInfo. miss면 None.
        """
        ...

    def get_valid_parses(self, lookups: list[ParseCacheLookup]) -> dict[int, ParsedInfo]:
        """Bulk read valid parse cache hits by media id."""
        ...

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
        """성공 파싱 결과를 저장한다. dto_json은 UI·후속 단계에 그대로 쓸 최종 DTO.

        Args:
            self: 저장소.
            media_file_id: `media_files.id`.
            parser_version: 기록용(운영 가시성). hit 판단은 서명에 포함된 버전.
            parse_input_signature: 무효화 서명.
            parsed: 최종 ParsedInfo(참고용; 진실은 dto_json).
            dto_json: compact JSON.
            parsed_title: 정규 컬럼(선택).
            parsed_title_normalized: 인덱스용 정규 제목(선택).
            parsed_year: 연도 숫자(선택).
            season_number: 시즌(선택).
            episode_start: 에피소드 시작(선택).
            episode_end: 에피소드 끝(선택).
            episode_count: 에피소드 수(선택).
            confidence: 신뢰도(선택).

        Returns:
            None.
        """
        ...

    def upsert_parse_ok_many(self, items: list[ParseCacheOkWrite]) -> None:
        """Bulk upsert successful parse cache rows."""
        ...

    def upsert_parse_error(
        self,
        *,
        media_file_id: int,
        parser_version: str,
        parse_input_signature: str,
        error_code: str | None,
        error_message: str | None,
    ) -> None:
        """실패 행을 저장한다. dto_json은 `{}` 고정. get_valid_parse는 hit하지 않는다.

        Args:
            self: 저장소.
            media_file_id: `media_files.id`.
            parser_version: 기록용.
            parse_input_signature: 당시 서명.
            error_code: 에러 코드(선택).
            error_message: 메시지(선택).

        Returns:
            None.
        """
        ...

    def upsert_parse_error_many(self, items: list[ParseCacheErrorWrite]) -> None:
        """Bulk upsert parse error cache rows."""
        ...

    def resolution_write_batch(self) -> AbstractContextManager[None]:
        """스캔 루프에서 다수의 `upsert_resolution` 커밋을 묶을 때 사용한다.

        Args:
            self: 이 저장소.

        Returns:
            컨텍스트 매니저.
        """
        ...

    def get_valid_resolution(self, media_file_id: int, signature: str) -> str | None:
        """서명이 일치하는 해상도 캐시를 반환한다.

        Args:
            self: 저장소.
            media_file_id: `media_files.id`.
            signature: 해상도 캐시 무효화 서명(size+mtime 기반).

        Returns:
            캐시된 해상도 문자열. miss면 None.
        """
        ...

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
            media_file_id: `media_files.id`.
            signature: 해상도 캐시 무효화 서명(size+mtime 기반).
            value: 저장할 해상도 라벨/WxH 값.
            source: 값 출처(`filename` 또는 `ffprobe` 등).

        Returns:
            None.
        """
        ...
