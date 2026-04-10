"""Title group contracts shared across domain, application, and adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

GroupType = Literal["parsed_title_norm", "sidecar"]
MemberRole = Literal["primary_video", "subtitle", "other"]


@dataclass(frozen=True, slots=True)
class TitleGroupingRow:
    """Input row used to compute title groups."""

    media_file_id: int
    parsed_title: str | None
    parsed_title_normalized: str | None
    parsed_year: int | None
    sidecar_group_key: str | None
    media_kind: str


@dataclass(frozen=True, slots=True)
class TitleGroupMember:
    """Title group member record."""

    media_file_id: int
    member_role: MemberRole
    score: float | None = None


@dataclass(frozen=True, slots=True)
class TitleGroupBundle:
    """Shared group bundle used for compute and persistence."""

    group_key: str
    group_type: GroupType
    canonical_title: str
    canonical_title_normalized: str
    tmdb_series_id: int | None
    group_confidence: float | None
    members: tuple[TitleGroupMember, ...]


@dataclass(frozen=True, slots=True)
class TitleGroupListRecord:
    """Read model for listing title groups."""

    id: int
    root_id: int
    group_key: str
    group_type: str
    member_count: int
    canonical_title: str | None
    canonical_title_normalized: str | None
