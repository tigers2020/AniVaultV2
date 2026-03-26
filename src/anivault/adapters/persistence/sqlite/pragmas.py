"""pragmas.py

SQLite 연결에 MVP PRAGMA을 적용한다. documents/sqlite_storage README 공통 전제.

Author: Pom Kim
"""

import sqlite3


def apply_pragmas(conn: sqlite3.Connection) -> None:
    """WAL·FK·동기화·캐시 관련 PRAGMA을 설정한다.

    Args:
        conn: SQLite 연결.

    Returns:
        None.
    """
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-64000")
