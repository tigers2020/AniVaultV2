"""Organize plan persistence contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OrganizePlanStatus = Literal["draft", "previewed", "applied", "failed", "rolled_back"]
OrganizePlanItemStatus = Literal["pending", "applied", "skipped", "failed", "rolled_back"]
OrganizeOperationKind = Literal["move", "rename", "copy", "link"]


@dataclass(frozen=True, slots=True)
class OrganizePlanHeaderRecord:
    id: int
    root_id: int
    plan_status: OrganizePlanStatus
    summary_json: str
    fs_log_path: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class OrganizePlanItemRecord:
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
    header: OrganizePlanHeaderRecord
    items: tuple[OrganizePlanItemRecord, ...]


@dataclass(frozen=True, slots=True)
class OrganizePlanAppendRow:
    src_path_norm: str
    dst_path_norm: str
    operation_kind: OrganizeOperationKind
    detail_json: str | None


@dataclass(frozen=True, slots=True)
class OrganizePlanListEntry:
    id: int
    plan_status: OrganizePlanStatus
    created_at: str
    updated_at: str
