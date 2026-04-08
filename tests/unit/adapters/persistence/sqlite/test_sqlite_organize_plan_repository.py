from __future__ import annotations

import threading
from pathlib import Path

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_organize_plan_repository import (
    SqliteOrganizePlanRepository,
)
from anivault.application.dto.organize_plan import OrganizePlanAppendRow


def test_sqlite_organize_plan_repository_round_trip(tmp_path: Path) -> None:
    conn = create_connection(tmp_path / "organize.db")
    lock = threading.Lock()
    roots = SqliteLibraryIndexRepository(conn, lock)
    repo = SqliteOrganizePlanRepository(conn, lock)
    try:
        root_id = roots.upsert_root(str(tmp_path / "library"))
        plan_id = repo.create_plan(root_id, "draft", '{"count":1}', fs_log_path=None)
        item_ids = repo.append_items(
            plan_id,
            (
                OrganizePlanAppendRow("src/a", "dst/a", "move", '{"kind":"move"}'),
                OrganizePlanAppendRow("src/b", "dst/b", "copy", None),
            ),
        )
        repo.update_plan_status(plan_id, "applied")
        repo.update_item_status(item_ids[0], "applied")
        repo.set_plan_fs_log_path(plan_id, "/logs/plan.log")

        bundle = repo.load_plan(plan_id)
        plans = repo.list_plans_for_root(root_id)

        assert bundle is not None
        assert bundle.header.plan_status == "applied"
        assert bundle.header.fs_log_path == "/logs/plan.log"
        assert [item.status for item in bundle.items] == ["applied", "pending"]
        assert plans[0].id == plan_id
    finally:
        conn.close()


def test_sqlite_organize_plan_repository_handles_empty_and_rollback(tmp_path: Path) -> None:
    conn = create_connection(tmp_path / "organize.db")
    lock = threading.Lock()
    roots = SqliteLibraryIndexRepository(conn, lock)
    repo = SqliteOrganizePlanRepository(conn, lock)
    try:
        root_id = roots.upsert_root(str(tmp_path / "library"))
        plan_id = repo.create_plan(root_id, "draft", "{}")
        assert repo.append_items(plan_id, ()) == ()
        assert repo.load_plan(plan_id + 1) is None

        first_item = repo.append_items(
            plan_id,
            (OrganizePlanAppendRow("src/a", "dst/a", "move", None),),
        )[0]
        repo.mark_plan_rolled_back(plan_id)
        bundle = repo.load_plan(plan_id)

        assert bundle is not None
        assert bundle.header.plan_status == "rolled_back"
        assert bundle.items[0].id == first_item
        assert bundle.items[0].status == "rolled_back"
    finally:
        conn.close()
