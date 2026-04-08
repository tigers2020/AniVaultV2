"""Application-wide repeated status and kind strings."""

from __future__ import annotations

from typing import Final

MATCH_STATUS_AUTO_MATCHED: Final[str] = "auto_matched"
MATCH_STATUS_CONFIRMED: Final[str] = "confirmed"
MATCH_STATUS_REJECTED: Final[str] = "rejected"

ORGANIZE_PLAN_STATUS_DRAFT: Final[str] = "draft"
ORGANIZE_PLAN_STATUS_PREVIEWED: Final[str] = "previewed"
ORGANIZE_PLAN_STATUS_APPLIED: Final[str] = "applied"
ORGANIZE_PLAN_STATUS_FAILED: Final[str] = "failed"
ORGANIZE_PLAN_STATUS_ROLLED_BACK: Final[str] = "rolled_back"

ORGANIZE_PLAN_ITEM_STATUS_PENDING: Final[str] = "pending"
ORGANIZE_PLAN_ITEM_STATUS_APPLIED: Final[str] = "applied"
ORGANIZE_PLAN_ITEM_STATUS_SKIPPED: Final[str] = "skipped"
ORGANIZE_PLAN_ITEM_STATUS_FAILED: Final[str] = "failed"
ORGANIZE_PLAN_ITEM_STATUS_ROLLED_BACK: Final[str] = "rolled_back"

ORGANIZE_OPERATION_KIND_MOVE: Final[str] = "move"
ORGANIZE_OPERATION_KIND_RENAME: Final[str] = "rename"
ORGANIZE_OPERATION_KIND_COPY: Final[str] = "copy"
ORGANIZE_OPERATION_KIND_LINK: Final[str] = "link"

GROUP_TYPE_PARSED_TITLE_NORM: Final[str] = "parsed_title_norm"
GROUP_TYPE_SIDECAR: Final[str] = "sidecar"

MEMBER_ROLE_PRIMARY_VIDEO: Final[str] = "primary_video"
MEMBER_ROLE_SUBTITLE: Final[str] = "subtitle"
MEMBER_ROLE_OTHER: Final[str] = "other"

PARSE_CACHE_STATUS_OK: Final[str] = "ok"
PARSE_CACHE_STATUS_ERROR: Final[str] = "error"

SCAN_SESSION_STATUS_SUCCESS: Final[str] = "success"
SCAN_SESSION_STATUS_FAILED: Final[str] = "failed"
SCAN_SESSION_STATUS_CANCELLED: Final[str] = "cancelled"

POSTER_ASSET_KIND_POSTER: Final[str] = "poster"
POSTER_ASSET_KIND_BACKDROP: Final[str] = "backdrop"
POSTER_ASSET_STATUS_READY: Final[str] = "ready"
POSTER_ASSET_STATUS_STALE: Final[str] = "stale"
POSTER_ASSET_STATUS_MISSING: Final[str] = "missing"
POSTER_ASSET_STATUS_FAILED: Final[str] = "failed"
