"""sqlite_cache_repository.py

`CacheRepository` — `app_kv` 테이블 백킹. JSON compact · TTL.

Author: Pom Kim
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text


def _is_expired(expires_at: str) -> bool:
    """만료 시각 문자열이 현재 UTC보다 이전인지 본다.

    Args:
        expires_at: SQLite에 저장된 시각 문자열.

    Returns:
        만료되었으면 True.
    """
    try:
        exp = expires_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(exp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
    except ValueError:
        return True
    now = datetime.now(UTC)
    return dt <= now


def _ttl_to_expires_at(ttl_seconds: int | None) -> str | None:
    """TTL 초를 만료 시각 문자열로 바꾼다.

    Args:
        ttl_seconds: 초. None이면 만료 없음.

    Returns:
        UTC ISO 문자열 또는 None.
    """
    if ttl_seconds is None:
        return None
    dt = datetime.now(UTC)
    return (dt + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


class SqliteCacheRepository:
    """소형 KV 캐시 — `app_kv`."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        """연결과 락을 받는다.

        Args:
            self: 저장소.
            conn: SQLite 연결.
            lock: 직렬화 락.

        Returns:
            None.
        """
        self._conn = conn
        self._lock = lock

    def get(self, key: str) -> object | None:
        """키를 조회한다. 만료된 행은 삭제하고 None을 반환한다.

        Args:
            self: 저장소.
            key: 키.

        Returns:
            역직렬화된 값. 없거나 만료면 None.
        """
        with self._lock:
            cur = self._conn.execute(
                "SELECT value_json, expires_at FROM app_kv WHERE key = ?",
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                self._conn.commit()
                return None
            raw, exp = str(row[0]), row[1]
            if exp is not None and _is_expired(str(exp)):
                self._conn.execute("DELETE FROM app_kv WHERE key = ?", (key,))
                self._conn.commit()
                return None
            self._conn.commit()
        try:
            decoded: object = json.loads(raw)
            return decoded
        except json.JSONDecodeError:
            with self._lock:
                self._conn.execute("DELETE FROM app_kv WHERE key = ?", (key,))
                self._conn.commit()
            return None

    def set(self, key: str, value: object, *, ttl_seconds: int | None = None) -> None:
        """키를 JSON으로 저장한다.

        Args:
            self: 저장소.
            key: 키.
            value: JSON 직렬화 가능 객체.
            ttl_seconds: 만료 TTL. None이면 무기한.

        Returns:
            None.
        """
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        vtype = type(value).__name__
        now = utc_now_sqlite_text()
        exp = _ttl_to_expires_at(ttl_seconds)
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO app_kv (key, value_json, value_type, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    value_type = excluded.value_type,
                    updated_at = excluded.updated_at,
                    expires_at = excluded.expires_at
                """,
                (key, payload, vtype, now, now, exp),
            )
            self._conn.commit()
