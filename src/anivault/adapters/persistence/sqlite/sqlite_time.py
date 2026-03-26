"""sqlite_time.py

DB TEXT 컬럼용 UTC 시각 문자열. implementation_policy ISO 8601 권장.

Author: Pom Kim
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


def utc_now_sqlite_text() -> str:
    """UTC 현재 시각을 SQLite TEXT에 넣을 문자열로 만든다.

    Args:
        없음.

    Returns:
        `YYYY-MM-DDTHH:MM:SSZ` 형식.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_plus_days_sqlite_text(days: int) -> str:
    """UTC 기준으로 지정 일 수 뒤 시각을 SQLite TEXT로 반환한다.

    Args:
        days: 더할 일 수(음수 불가 가정).

    Returns:
        `YYYY-MM-DDTHH:MM:SSZ` 형식.
    """
    return (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_utc_sqlite_text_expired(expires_at: str, *, now: datetime | None = None) -> bool:
    """저장된 만료 시각 문자열이 현재(UTC)보다 이전인지 본다.

    Args:
        expires_at: `utc_now_sqlite_text`/`utc_plus_days_sqlite_text` 형식(`Z` 접미).
        now: 테스트용 고정 시각. None이면 `datetime.now(UTC)`.

    Returns:
        만료였거나 파싱 실패 시 True.
    """
    s = (expires_at or "").strip()
    if not s:
        return True
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(s)
        ref = now if now is not None else datetime.now(UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt <= ref
    except ValueError:
        return True
