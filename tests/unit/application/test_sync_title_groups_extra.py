from __future__ import annotations

from anivault.application.dto.title_groups import (
    TitleGroupListRecord,
    TitleGroupMemberSync,
    TitleGroupSyncBundle,
)
from anivault.application.use_cases.sync_title_groups import _computed_to_bundle, make_execute
from anivault.domain.services.title_grouping import (
    TitleGroupComputed,
    TitleGroupingInputRow,
    TitleGroupMemberComputed,
)


def test_computed_to_bundle_maps_domain_result() -> None:
    bundle = _computed_to_bundle(
        TitleGroupComputed(
            group_key="group",
            group_type="parsed_title_norm",
            canonical_title="Show",
            canonical_title_normalized="show",
            members=(TitleGroupMemberComputed(1, "primary_video", 0.9),),
        )
    )

    assert bundle.group_key == "group"
    assert bundle.members == (TitleGroupMemberSync(1, "primary_video", 0.9),)


def test_make_execute_loads_rows_computes_groups_and_replaces(monkeypatch) -> None:
    class _Repo:
        def __init__(self) -> None:
            self.replaced: tuple[int, list[TitleGroupSyncBundle]] | None = None

        def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingInputRow]:
            return [
                TitleGroupingInputRow(
                    media_file_id=1,
                    parsed_title="Show",
                    parsed_title_normalized="show",
                    parsed_year=None,
                    sidecar_group_key=None,
                    media_kind="video",
                )
            ]

        def get_group_ids_for_path_norms(
            self,
            root_id: int,
            path_norms: list[str],
        ) -> dict[str, int]:
            return {}

        def replace_root_title_groups(
            self,
            root_id: int,
            bundles: list[TitleGroupSyncBundle],
        ) -> None:
            self.replaced = (root_id, bundles)

        def replace_group_members(
            self,
            group_id: int,
            members: list[TitleGroupMemberSync],
        ) -> None:
            return None

        def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
            return []

        def get_group_id(self, root_id: int, group_key: str) -> int | None:
            return None

        def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None:
            return None

    repo = _Repo()
    computed = [
        TitleGroupComputed(
            group_key="group",
            group_type="parsed_title_norm",
            canonical_title="Show",
            canonical_title_normalized="show",
            members=(TitleGroupMemberComputed(1, "primary_video", 0.9),),
        )
    ]
    monkeypatch.setattr(
        "anivault.application.use_cases.sync_title_groups.compute_title_groups",
        lambda rows: computed,
    )

    make_execute(repo)(7)

    assert repo.replaced is not None
    root_id, bundles = repo.replaced
    assert root_id == 7
    assert len(bundles) == 1
