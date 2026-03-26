"""connection.py

SQLite 연결 팩토리: 부모 디렉터리 생성, PRAGMA, 마이그레이션.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from anivault.adapters.persistence.sqlite.db_path import (
    default_anivault_db_path,
    ensure_db_parent_dir,
)
from anivault.adapters.persistence.sqlite.migrate import apply_pending_migrations
from anivault.adapters.persistence.sqlite.pragmas import apply_pragmas


def create_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """AniVault용 SQLite 연결을 연다. PRAGMA·마이그레이션까지 적용한다.

    Args:
        db_path: DB 파일 경로. None이면 `default_anivault_db_path()`.

    Returns:
        `check_same_thread=False` 인 연결.

    Raises:
        sqlite3.Error: 열기 또는 마이그레이션 실패 시.
    """
    path = db_path if db_path is not None else default_anivault_db_path()
    ensure_db_parent_dir(path)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    try:
        apply_pragmas(conn)
        apply_pending_migrations(conn)
    except Exception:
        conn.close()
        raise
    return conn
