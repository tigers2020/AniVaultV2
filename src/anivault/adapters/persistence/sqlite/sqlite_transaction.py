"""Shared SQLite transaction helpers."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def sqlite_transaction(conn: sqlite3.Connection) -> Iterator[None]:
    """Run a block inside ``BEGIN/COMMIT`` with rollback on failure."""

    conn.execute("BEGIN")
    try:
        yield
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
