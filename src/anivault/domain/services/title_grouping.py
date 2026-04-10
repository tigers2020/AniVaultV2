"""Title group computation for cached parse results."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence

from anivault.contracts.title_groups import (
    GroupType,
    MemberRole,
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupMember,
)


def _member_role_for_media_kind(media_kind: str) -> MemberRole:
    if media_kind == "video":
        return "primary_video"
    if media_kind == "subtitle":
        return "subtitle"
    return "other"


def _bucket_key_for_row(row: TitleGroupingRow) -> tuple[GroupType, str] | None:
    sidecar_key = (row.sidecar_group_key or "").strip()
    if sidecar_key:
        return "sidecar", f"sc:{sidecar_key}"
    normalized = (row.parsed_title_normalized or "").strip()
    if not normalized:
        return None
    return "parsed_title_norm", f"ptn:{normalized}"


def _canonical_from_row(row: TitleGroupingRow) -> tuple[str, str]:
    parsed_title = (row.parsed_title or "").strip()
    normalized = (row.parsed_title_normalized or "").strip()
    return (parsed_title if parsed_title else normalized, normalized)


def _pick_representative(rows: list[TitleGroupingRow]) -> TitleGroupingRow:
    def _media_kind_priority(media_kind: str) -> int:
        if media_kind == "video":
            return 0
        if media_kind == "subtitle":
            return 1
        return 2

    return sorted(
        rows,
        key=lambda row: (_media_kind_priority(row.media_kind), row.media_file_id),
    )[0]


def compute_title_groups(rows: Sequence[TitleGroupingRow]) -> list[TitleGroupBundle]:
    """Group parsed rows and return persistence-ready group bundles."""

    buckets: OrderedDict[tuple[GroupType, str], list[TitleGroupingRow]] = OrderedDict()
    for row in rows:
        bucket_key = _bucket_key_for_row(row)
        if bucket_key is None:
            continue
        group_type, group_key = bucket_key
        buckets.setdefault((group_type, group_key), []).append(row)

    groups: list[TitleGroupBundle] = []
    for (group_type, group_key), bucket_rows in buckets.items():
        representative = _pick_representative(bucket_rows)
        canonical_title, canonical_title_normalized = _canonical_from_row(representative)
        members = tuple(
            TitleGroupMember(
                media_file_id=row.media_file_id,
                member_role=_member_role_for_media_kind(row.media_kind),
                score=None,
            )
            for row in sorted(bucket_rows, key=lambda item: item.media_file_id)
        )
        groups.append(
            TitleGroupBundle(
                group_key=group_key,
                group_type=group_type,
                canonical_title=canonical_title,
                canonical_title_normalized=canonical_title_normalized,
                tmdb_series_id=None,
                group_confidence=None,
                members=members,
            )
        )
    groups.sort(key=lambda group: group.group_key)
    return groups
