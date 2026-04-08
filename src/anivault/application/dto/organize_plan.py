"""organize_plan.py

정리 플랜(organize_plans / organize_plan_items)용 DTO. summary_json·detail_json 책임 분리.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OrganizePlanStatus = Literal["draft", "previewed", "applied", "failed", "rolled_back"]

OrganizePlanItemStatus = Literal["pending", "applied", "skipped", "failed", "rolled_back"]

OrganizeOperationKind = Literal["move", "rename", "copy", "link"]


@dataclass(frozen=True, slots=True)
class OrganizePlanHeaderRecord:
    """organize_plans 행 요약."""

    id: int
    root_id: int
    plan_status: OrganizePlanStatus
    summary_json: str
    fs_log_path: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class OrganizePlanItemRecord:
    """organize_plan_items 행."""

    id: int
    plan_id: int
    src_path_norm: str
    dst_path_norm: str
    operation_kind: OrganizeOperationKind
    status: OrganizePlanItemStatus
    detail_json: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class OrganizePlanBundle:
    """플랜 헤더와 아이템(load_plan). 아이템은 id 오름차순."""

    header: OrganizePlanHeaderRecord
    items: tuple[OrganizePlanItemRecord, ...]


@dataclass(frozen=True, slots=True)
class OrganizePlanAppendRow:
    """append_items 한 행."""

    src_path_norm: str
    dst_path_norm: str
    operation_kind: OrganizeOperationKind
    detail_json: str | None


@dataclass(frozen=True, slots=True)
class OrganizePlanListEntry:
    """list_plans_for_root 한 줄."""

    id: int
    plan_status: OrganizePlanStatus
    created_at: str
    updated_at: str
