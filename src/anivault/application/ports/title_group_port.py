"""Port for title group persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.contracts.title_groups import (
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)


@runtime_checkable
class TitleGroupRepository(Protocol):
    """Persistence contract for title groups and their members."""

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingRow]: ...

    def get_group_ids_for_path_norms(
        self,
        root_id: int,
        path_norms: list[str],
    ) -> dict[str, int]: ...

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupBundle]) -> None: ...

    def replace_group_members(
        self,
        group_id: int,
        members: list[TitleGroupMember],
    ) -> None: ...

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]: ...

    def get_group_id(self, root_id: int, group_key: str) -> int | None: ...

    def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None: ...
