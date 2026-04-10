"""Serialization helpers for ParsedInfo."""

from __future__ import annotations

import json
from dataclasses import asdict

from anivault.domain.models import ParsedInfo


def parsed_info_to_compact_json(parsed: ParsedInfo) -> str:
    """Serialize ParsedInfo into compact JSON."""

    return json.dumps(asdict(parsed), ensure_ascii=False, separators=(",", ":"))


def parsed_info_from_compact_json(raw: str) -> ParsedInfo:
    """Deserialize compact JSON into ParsedInfo."""

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise TypeError("parsed JSON must be an object")
    return ParsedInfo(
        title=str(data.get("title", "")),
        parse_group=str(data.get("parse_group", "")),
        year=str(data.get("year", "")),
        season=str(data.get("season", "")),
        episode=str(data.get("episode", "")),
        episode_numbers=[
            int(value)
            for value in data.get("episode_numbers", [])
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit())
        ],
        resolution=str(data.get("resolution", "")),
    )
