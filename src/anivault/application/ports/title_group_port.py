"""title_group_port.py

title_groups / title_group_members 저장·조회 포트.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.application.dto.title_groups import (
    TitleGroupListRecord,
    TitleGroupMemberSync,
    TitleGroupSyncBundle,
)
from anivault.domain.services.title_grouping import TitleGroupingInputRow


@runtime_checkable
class TitleGroupRepository(Protocol):
    """작품 단위 그룹 영속화. 동기화는 루트별 full rebuild 권장."""

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingInputRow]:
        """`parse_status=ok` 이고 삭제되지 않은 미디어·캐시 행을 그룹 입력으로 반환한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.

        Returns:
            `TitleGroupingInputRow` 목록.
        """
        ...

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupSyncBundle]) -> None:
        """단일 트랜잭션에서 루트 소속 기존 그룹을 모두 지우고 새 그룹·멤버를 쓴다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            bundles: 그룹·멤버 묶음(도메인 계산 결과).

        Returns:
            None.
        """
        ...

    def replace_group_members(
        self,
        group_id: int,
        members: list[TitleGroupMemberSync],
    ) -> None:
        """한 그룹의 멤버를 전부 교체한다(DELETE 후 INSERT, 단일 트랜잭션).

        Args:
            self: 저장소.
            group_id: `title_groups.id`.
            members: 새 멤버 목록.

        Returns:
            None.
        """
        ...

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
        """루트 소속 그룹 메타를 조회한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.

        Returns:
            `TitleGroupListRecord` 목록.
        """
        ...

    def get_group_id(self, root_id: int, group_key: str) -> int | None:
        """루트·`group_key`로 `title_groups.id`를 조회한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            group_key: `title_groups.group_key` 와 동일 문자열.

        Returns:
            그룹 id. 없으면 None.
        """
        ...

    def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None:
        """멤버 미디어의 `path_norm`으로 소속 그룹 id를 찾는다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            path_norm: `normalize_path_key` 결과.

        Returns:
            `title_groups.id`. 없으면 None.
        """
        ...
