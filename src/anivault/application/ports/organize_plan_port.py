"""Port for organize plan persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.contracts.organize_plan import (
    OrganizePlanAppendRow,
    OrganizePlanBundle,
    OrganizePlanItemStatus,
    OrganizePlanListEntry,
    OrganizePlanStatus,
)


@runtime_checkable
class OrganizePlanRepository(Protocol):
    def create_plan(
        self,
        root_id: int,
        plan_status: OrganizePlanStatus,
        summary_json: str,
        *,
        fs_log_path: str | None = None,
    ) -> int: ...

    def append_items(
        self, plan_id: int, rows: tuple[OrganizePlanAppendRow, ...]
    ) -> tuple[int, ...]: ...

    def update_plan_status(
        self,
        plan_id: int,
        plan_status: OrganizePlanStatus,
    ) -> None: ...

    def update_item_status(
        self,
        item_id: int,
        status: OrganizePlanItemStatus,
    ) -> None: ...

    def set_plan_fs_log_path(
        self,
        plan_id: int,
        fs_log_path: str | None,
    ) -> None: ...

    def load_plan(self, plan_id: int) -> OrganizePlanBundle | None: ...

    def list_plans_for_root(
        self,
        root_id: int,
        *,
        limit: int = 100,
    ) -> tuple[OrganizePlanListEntry, ...]: ...

    def mark_plan_rolled_back(self, plan_id: int) -> None: ...
