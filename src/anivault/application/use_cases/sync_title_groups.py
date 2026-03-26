"""sync_title_groups.py

파싱 캐시 반영 후 title_groups 를 루트 단위로 재구성한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable

from anivault.application.dto.title_groups import TitleGroupMemberSync, TitleGroupSyncBundle
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.domain.services.title_grouping import TitleGroupComputed, compute_title_groups


def _computed_to_bundle(c: TitleGroupComputed) -> TitleGroupSyncBundle:
    """도메인 결과를 저장 DTO 로 바꾼다.

    Args:
        c: 계산된 그룹.

    Returns:
        `TitleGroupSyncBundle`.
    """
    return TitleGroupSyncBundle(
        group_key=c.group_key,
        group_type=c.group_type,
        canonical_title=c.canonical_title,
        canonical_title_normalized=c.canonical_title_normalized,
        tmdb_series_id=None,
        group_confidence=None,
        members=tuple(
            TitleGroupMemberSync(m.media_file_id, m.member_role, m.score) for m in c.members
        ),
    )


def make_execute(
    title_groups: TitleGroupRepository,
) -> Callable[[int], None]:
    """TitleGroupRepository 가 주입된 동기화 실행 함수를 만든다.

    Args:
        title_groups: 그룹 저장소.

    Returns:
        `(root_id) -> None` 클로저.
    """

    def execute(root_id: int) -> None:
        """루트에 대해 그룹을 전부 다시 계산·저장한다.

        Args:
            root_id: `library_roots.id`.

        Returns:
            None.
        """
        rows = title_groups.load_rows_for_grouping(root_id)
        computed = compute_title_groups(rows)
        bundles = [_computed_to_bundle(c) for c in computed]
        title_groups.replace_root_title_groups(root_id, bundles)

    return execute
