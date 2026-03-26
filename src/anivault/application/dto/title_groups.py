"""title_groups.py

SQLite title_groups 동기화용 DTO.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

GroupTypeDto = Literal["parsed_title_norm", "sidecar"]
MemberRoleDto = Literal["primary_video", "subtitle", "other"]


@dataclass(frozen=True)
class TitleGroupMemberSync:
    """멤버 한 명을 저장소에 쓸 때 쓰는 형태."""

    media_file_id: int
    member_role: MemberRoleDto
    score: float | None = None


@dataclass(frozen=True)
class TitleGroupSyncBundle:
    """한 그룹과 멤버 전체."""

    group_key: str
    group_type: GroupTypeDto
    canonical_title: str
    canonical_title_normalized: str
    tmdb_series_id: int | None
    group_confidence: float | None
    members: tuple[TitleGroupMemberSync, ...]


@dataclass(frozen=True)
class TitleGroupListRecord:
    """list_title_groups_for_root 결과 한 행."""

    id: int
    root_id: int
    group_key: str
    group_type: str
    member_count: int
    canonical_title: str | None
    canonical_title_normalized: str | None
