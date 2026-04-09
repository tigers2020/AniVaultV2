"""organize_plan_port.py

정리 플랜 영속화 포트(organize_plans / organize_plan_items).

Author: Pom Kim
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.application.dto.organize_plan import (
    OrganizePlanAppendRow,
    OrganizePlanBundle,
    OrganizePlanItemStatus,
    OrganizePlanListEntry,
    OrganizePlanStatus,
)


@runtime_checkable
class OrganizePlanRepository(Protocol):
    """사용자가 재열람할 수 있는 정리 플랜·항목·상태 저장.

    `load_plan`·`mark_plan_rolled_back`는 어댑터·단위 테스트에서 검증되나,
    롤백·히스토리 UI가 없어 현재 application 유스케이스에서는 호출하지 않는다.
    """

    def create_plan(
        self,
        root_id: int,
        plan_status: OrganizePlanStatus,
        summary_json: str,
        *,
        fs_log_path: str | None = None,
    ) -> int:
        """플랜 헤더를 만들고 `organize_plans.id`를 반환한다.

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            plan_status: 초기 상태.
            summary_json: 플랜 전체 요약 JSON.
            fs_log_path: Fs 로그 파일 경로(선택).

        Returns:
            새 플랜 ID.
        """
        ...

    def append_items(
        self, plan_id: int, rows: tuple[OrganizePlanAppendRow, ...]
    ) -> tuple[int, ...]:
        """아이템을 배치 삽입하고, 삽입 순서와 동일한 id 목록을 반환한다.

        Args:
            self: 저장소.
            plan_id: 부모 플랜 ID.
            rows: 삽입 행(각각 `pending`으로 저장).

        Returns:
            새 아이템 id들.
        """
        ...

    def update_plan_status(
        self,
        plan_id: int,
        plan_status: OrganizePlanStatus,
    ) -> None:
        """플랜 상태를 갱신한다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.
            plan_status: 새 상태.

        Returns:
            None.
        """
        ...

    def update_item_status(
        self,
        item_id: int,
        status: OrganizePlanItemStatus,
    ) -> None:
        """단일 아이템 상태를 갱신한다.

        Args:
            self: 저장소.
            item_id: `organize_plan_items.id`.
            status: 새 상태.

        Returns:
            None.
        """
        ...

    def set_plan_fs_log_path(
        self,
        plan_id: int,
        fs_log_path: str | None,
    ) -> None:
        """Fs 로그 파일 경로를 기록한다.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.
            fs_log_path: 로그 경로 또는 None.

        Returns:
            None.
        """
        ...

    def load_plan(self, plan_id: int) -> OrganizePlanBundle | None:
        """플랜과 아이템을 조회한다. 아이템은 id 오름차순.

        Args:
            self: 저장소.
            plan_id: 플랜 ID.

        Returns:
            번들 또는 없으면 None.
        """
        ...

    def list_plans_for_root(
        self,
        root_id: int,
        *,
        limit: int = 100,
    ) -> tuple[OrganizePlanListEntry, ...]:
        """루트별 최근 플랜 목록(간단).

        Args:
            self: 저장소.
            root_id: `library_roots.id`.
            limit: 최대 개수.

        Returns:
            엔트리 튜플.
        """
        ...

    def mark_plan_rolled_back(self, plan_id: int) -> None:
        """플랜을 `rolled_back`으로, 소속 아이템을 모두 `rolled_back`으로 맞춘다(6a 일관성).

        Args:
            self: 저장소.
            plan_id: 플랜 ID.

        Returns:
            None.
        """
        ...
