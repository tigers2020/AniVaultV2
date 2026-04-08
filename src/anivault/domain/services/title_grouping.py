"""title_grouping.py

title_groups 동기화용 그룹 키·멤버십 계산(도메인 전용).

Author: Pom Kim
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

GroupTypeStr = Literal["parsed_title_norm", "sidecar"]
MemberRoleStr = Literal["primary_video", "subtitle", "other"]


@dataclass(frozen=True)
class TitleGroupingInputRow:
    """그룹 입력 한 행: 인덱스·파싱 캐시에서 채운다."""

    media_file_id: int
    parsed_title: str | None
    parsed_title_normalized: str | None
    parsed_year: int | None
    sidecar_group_key: str | None
    media_kind: str


@dataclass(frozen=True)
class TitleGroupMemberComputed:
    """그룹 멤버 한 명."""

    media_file_id: int
    member_role: MemberRoleStr
    score: float | None = None


@dataclass(frozen=True)
class TitleGroupComputed:
    """persist 전 그룹 단위 결과."""

    group_key: str
    group_type: GroupTypeStr
    canonical_title: str
    canonical_title_normalized: str
    members: tuple[TitleGroupMemberComputed, ...]


def _member_role_for_media_kind(media_kind: str) -> MemberRoleStr:
    """미디어 분류를 member_role 로 매핑한다.

    Args:
        media_kind: 인덱스 `media_kind` 문자열.

    Returns:
        `primary_video`, `subtitle`, `other`.
    """
    if media_kind == "video":
        return "primary_video"
    if media_kind == "subtitle":
        return "subtitle"
    return "other"


def _bucket_key_for_row(row: TitleGroupingInputRow) -> tuple[GroupTypeStr, str] | None:
    """sidecar 우선 후 ptn 버킷 키를 만든다. 그룹에 넣을 수 없으면 None.

    Args:
        row: 입력 행.

    Returns:
        `(group_type, full_group_key)` — `sc:...` 또는 `ptn:...`.
    """
    sc = (row.sidecar_group_key or "").strip()
    if sc:
        return ("sidecar", f"sc:{sc}")
    norm = (row.parsed_title_normalized or "").strip()
    if not norm:
        return None
    return ("parsed_title_norm", f"ptn:{norm}")


def _canonical_from_row(row: TitleGroupingInputRow) -> tuple[str, str]:
    """canonical_title 과 canonical_title_normalized 를 한 행에서 채운다.

    Args:
        row: 대표 후보 행.

    Returns:
        `(canonical_title, canonical_title_normalized)`.
    """
    pt = (row.parsed_title or "").strip()
    ptn = (row.parsed_title_normalized or "").strip()
    title = pt if pt else ptn
    return title, ptn


def _pick_representative(
    rows: list[TitleGroupingInputRow],
) -> TitleGroupingInputRow:
    """비디오 우선·media_file_id 로 tie-break 대표 행을 고른다.

    Args:
        rows: 동일 버킷 멤버 원본 행.

    Returns:
        대표 `TitleGroupingInputRow`.
    """

    def _media_kind_priority(media_kind: str) -> int:
        if media_kind == "video":
            return 0
        if media_kind == "subtitle":
            return 1
        return 2

    sorted_rows = sorted(
        rows,
        key=lambda r: (
            _media_kind_priority(r.media_kind),
            r.media_file_id,
        ),
    )
    return sorted_rows[0]


def compute_title_groups(rows: Sequence[TitleGroupingInputRow]) -> list[TitleGroupComputed]:
    """입력 행을 그룹 키로 묶어 `TitleGroupComputed` 목록을 만든다.

    입력 순서는 버킷 삽입 순서에만 영향을 주며, 멤버·대표는 결정적이다.

    Args:
        rows: `parse_status=ok` 등 필터링된 인덱스·캐시 행.

    Returns:
        그룹 목록(정렬된 group_key 순).
    """
    buckets: OrderedDict[tuple[GroupTypeStr, str], list[TitleGroupingInputRow]] = OrderedDict()
    for row in rows:
        bk = _bucket_key_for_row(row)
        if bk is None:
            continue
        gtype, gkey = bk
        buckets.setdefault((gtype, gkey), []).append(row)

    out: list[TitleGroupComputed] = []
    for (gtype, gkey), bucket_rows in buckets.items():
        rep = _pick_representative(bucket_rows)
        ct, ctn = _canonical_from_row(rep)
        members: list[TitleGroupMemberComputed] = []
        for r in sorted(bucket_rows, key=lambda x: x.media_file_id):
            members.append(
                TitleGroupMemberComputed(
                    media_file_id=r.media_file_id,
                    member_role=_member_role_for_media_kind(r.media_kind),
                    score=None,
                ),
            )
        out.append(
            TitleGroupComputed(
                group_key=gkey,
                group_type=gtype,
                canonical_title=ct,
                canonical_title_normalized=ctn,
                members=tuple(members),
            ),
        )
    out.sort(key=lambda g: g.group_key)
    return out
