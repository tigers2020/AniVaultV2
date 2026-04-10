from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from anivault.adapters.persistence.sqlite.sqlite_transaction import sqlite_transaction


def test_sqlite_transaction_commits_on_success() -> None:
    conn = MagicMock()

    with sqlite_transaction(conn):
        conn.execute("SELECT 1")

    conn.execute.assert_any_call("BEGIN")
    conn.commit.assert_called_once()
    conn.rollback.assert_not_called()


def test_sqlite_transaction_rolls_back_on_error() -> None:
    conn = MagicMock()

    with pytest.raises(RuntimeError), sqlite_transaction(conn):
        raise RuntimeError("boom")

    conn.execute.assert_called_once_with("BEGIN")
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
