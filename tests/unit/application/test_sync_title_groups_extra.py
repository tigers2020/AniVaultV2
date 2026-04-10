from __future__ import annotations

from anivault.application.use_cases.sync_title_groups import make_execute
from anivault.contracts.title_groups import (
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)


def test_make_execute_loads_rows_computes_groups_and_replaces(monkeypatch) -> None:
    class _Repo:
        def __init__(self) -> None:
            self.replaced: tuple[int, list[TitleGroupBundle]] | None = None

        def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingRow]:
            return [
                TitleGroupingRow(
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
            bundles: list[TitleGroupBundle],
        ) -> None:
            self.replaced = (root_id, bundles)

        def replace_group_members(
            self,
            group_id: int,
            members: list[TitleGroupMember],
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
        TitleGroupBundle(
            group_key="group",
            group_type="parsed_title_norm",
            canonical_title="Show",
            canonical_title_normalized="show",
            tmdb_series_id=None,
            group_confidence=None,
            members=(TitleGroupMember(1, "primary_video", 0.9),),
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
    assert bundles == computed
