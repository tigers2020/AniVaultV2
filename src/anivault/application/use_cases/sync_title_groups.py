"""Rebuild title groups for a library root from parse cache state."""

from __future__ import annotations

from collections.abc import Callable

from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.domain.services.title_grouping import compute_title_groups


def make_execute(title_groups: TitleGroupRepository) -> Callable[[int], None]:
    """Create the title-group sync use case."""

    def execute(root_id: int) -> None:
        rows = title_groups.load_rows_for_grouping(root_id)
        title_groups.replace_root_title_groups(root_id, compute_title_groups(rows))

    return execute
