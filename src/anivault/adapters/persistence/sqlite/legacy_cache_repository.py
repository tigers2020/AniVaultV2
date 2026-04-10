"""Legacy SQLite ``app_kv`` cache adapter kept for compatibility."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text


def _is_expired(expires_at: str) -> bool:
    """Return whether an ISO-style UTC expiration timestamp is in the past."""

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
    """Convert a TTL in seconds into persisted UTC expiration text."""

    if ttl_seconds is None:
        return None
    dt = datetime.now(UTC)
    return (dt + timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


class SqliteCacheRepository:
    """Small JSON-backed KV cache stored in the legacy ``app_kv`` table."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        self._conn = conn
        self._lock = lock

    def get(self, key: str) -> object | None:
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
