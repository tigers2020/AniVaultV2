from __future__ import annotations

from anivault.domain.services.title_grouping import (
    TitleGroupingInputRow,
    _bucket_key_for_row,
    _canonical_from_row,
    _member_role_for_media_kind,
    _pick_representative,
    compute_title_groups,
)


def _row(
    media_file_id: int,
    *,
    parsed_title: str | None = "Show",
    parsed_title_normalized: str | None = "show",
    sidecar_group_key: str | None = None,
    media_kind: str = "video",
) -> TitleGroupingInputRow:
    return TitleGroupingInputRow(
        media_file_id=media_file_id,
        parsed_title=parsed_title,
        parsed_title_normalized=parsed_title_normalized,
        parsed_year=2024,
        sidecar_group_key=sidecar_group_key,
        media_kind=media_kind,
    )


def test_grouping_helpers_cover_bucket_canonical_and_priority() -> None:
    assert _member_role_for_media_kind("video") == "primary_video"
    assert _member_role_for_media_kind("subtitle") == "subtitle"
    assert _member_role_for_media_kind("audio") == "other"

    assert _bucket_key_for_row(_row(1, sidecar_group_key="grp")) == ("sidecar", "sc:grp")
    assert _bucket_key_for_row(_row(1, sidecar_group_key=None)) == ("parsed_title_norm", "ptn:show")
    assert _bucket_key_for_row(_row(1, parsed_title_normalized="  ")) is None

    assert _canonical_from_row(_row(1, parsed_title="Shown", parsed_title_normalized="shown")) == (
        "Shown",
        "shown",
    )
    assert _canonical_from_row(_row(1, parsed_title=" ", parsed_title_normalized="shown")) == (
        "shown",
        "shown",
    )

    representative = _pick_representative(
        [
            _row(30, media_kind="other"),
            _row(20, media_kind="subtitle"),
            _row(10, media_kind="video"),
        ]
    )
    assert representative.media_file_id == 10


def test_compute_title_groups_sorts_members_and_group_keys() -> None:
    rows = [
        _row(5, parsed_title="Show", parsed_title_normalized="show"),
        _row(2, parsed_title="Show", parsed_title_normalized="show", media_kind="subtitle"),
        _row(9, parsed_title="Movie", parsed_title_normalized="movie", sidecar_group_key="bundle"),
        _row(1, parsed_title=None, parsed_title_normalized=" "),
    ]

    groups = compute_title_groups(rows)

    assert [group.group_key for group in groups] == ["ptn:show", "sc:bundle"]
    assert [member.media_file_id for member in groups[0].members] == [2, 5]
    assert groups[0].canonical_title == "Show"
    assert groups[0].members[0].member_role == "subtitle"
    assert groups[1].group_type == "sidecar"
