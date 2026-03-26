"""migrate.py

schema_migrations 기준 마이그레이션 적용. 버전별 스크립트 + 기록은 트랜잭션 단위.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from importlib import resources


def _migration_001_sql() -> str:
    """001_initial.sql 본문을 패키지 리소스에서 읽는다.

    Args:
        없음.

    Returns:
        SQL 스크립트 문자열.
    """
    pkg = "anivault.adapters.persistence.sqlite.migrations"
    ref = resources.files(pkg).joinpath("001_initial.sql")
    return ref.read_text(encoding="utf-8")


def _migration_002_sql() -> str:
    """002_parse_cache.sql 본문을 패키지 리소스에서 읽는다.

    Args:
        없음.

    Returns:
        SQL 스크립트 문자열.
    """
    pkg = "anivault.adapters.persistence.sqlite.migrations"
    ref = resources.files(pkg).joinpath("002_parse_cache.sql")
    return ref.read_text(encoding="utf-8")


def _migration_003_sql() -> str:
    """003_title_groups.sql 본문을 패키지 리소스에서 읽는다.

    Args:
        없음.

    Returns:
        SQL 스크립트 문자열.
    """
    pkg = "anivault.adapters.persistence.sqlite.migrations"
    ref = resources.files(pkg).joinpath("003_title_groups.sql")
    return ref.read_text(encoding="utf-8")


def _migration_004_sql() -> str:
    """004_tmdb_cache.sql 본문을 패키지 리소스에서 읽는다.

    Args:
        없음.

    Returns:
        SQL 스크립트 문자열.
    """
    pkg = "anivault.adapters.persistence.sqlite.migrations"
    ref = resources.files(pkg).joinpath("004_tmdb_cache.sql")
    return ref.read_text(encoding="utf-8")


def _migrations() -> list[tuple[int, str, Callable[[], str]]]:
    """적용 순서대로 (버전, 이름, SQL 로더) 목록을 반환한다.

    Args:
        없음.

    Returns:
        마이그레이션 정의 목록.
    """
    return [
        (1, "001_initial", _migration_001_sql),
        (2, "002_parse_cache", _migration_002_sql),
        (3, "003_title_groups", _migration_003_sql),
        (4, "004_tmdb_cache", _migration_004_sql),
    ]


def apply_pending_migrations(conn: sqlite3.Connection) -> None:
    """적용되지 않은 마이그레이션을 순서대로 실행한다.

    Args:
        conn: SQLite 연결(이미 PRAGMA 적용 후).

    Returns:
        None.

    Raises:
        sqlite3.Error: SQL 실행 실패 시.
    """
    for version, name, load_sql in _migrations():
        cur = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'",
        )
        if cur.fetchone() is not None:
            cur = conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?",
                (version,),
            )
            if cur.fetchone() is not None:
                continue

        sql = load_sql()
        conn.execute("BEGIN")
        try:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (version, name),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
