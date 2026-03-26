"""parse_serde.py

ParsedInfo compact JSON 직렬화. implementation_policy §6 (UTF-8, compact, null 유지).

Author: Pom Kim
"""

from __future__ import annotations

import json
from dataclasses import asdict

from anivault.application.dto.parse import ParsedInfo


def parsed_info_to_compact_json(parsed: ParsedInfo) -> str:
    """최종 ParsedInfo를 DB용 compact JSON 문자열로 만든다.

    Args:
        parsed: 직렬화할 파싱 결과.

    Returns:
        UTF-8 compact JSON 텍스트.
    """
    return json.dumps(asdict(parsed), ensure_ascii=False, separators=(",", ":"))


def parsed_info_from_compact_json(raw: str) -> ParsedInfo:
    """compact JSON을 ParsedInfo로 복원한다.

    Args:
        raw: DB 또는 캐시 TEXT.

    Returns:
        복원된 ParsedInfo.

    Raises:
        json.JSONDecodeError: JSON이 아닐 때.
        TypeError: 필드 타입이 맞지 않을 때.
    """
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("parsed JSON must be an object")
    return ParsedInfo(
        title=str(data.get("title", "")),
        parse_group=str(data.get("parse_group", "")),
        year=str(data.get("year", "")),
        season=str(data.get("season", "")),
        episode=str(data.get("episode", "")),
        resolution=str(data.get("resolution", "")),
    )
