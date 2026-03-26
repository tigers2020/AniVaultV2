"""sqlite_time.py

DB TEXT 컬럼용 UTC 시각 문자열. implementation_policy ISO 8601 권장.

Author: Pom Kim
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now_sqlite_text() -> str:
    """UTC 현재 시각을 SQLite TEXT에 넣을 문자열로 만든다.

    Args:
        없음.

    Returns:
        `YYYY-MM-DDTHH:MM:SSZ` 형식.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
