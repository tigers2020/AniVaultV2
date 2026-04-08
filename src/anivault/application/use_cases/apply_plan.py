"""apply_plan.py

계획을 로그에 저장한 뒤 dry_run이 아니면 파일을 이동한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import cast

from anivault.application.dto.plan import ApplyInput, ApplyResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.file_repository import FileRepository
from anivault.application.ports.library_index_port import LibraryIndexRepository
from anivault.application.ports.operation_log_port import OperationLogRepository
from anivault.application.ports.organize_plan_port import OrganizePlanRepository

ApplyProgressCallback = Callable[[ProgressEvent], None]


def make_apply_execute(
    file_repo: FileRepository,
    operation_log_factory: Callable[[Path], OperationLogRepository],
    *,
    library_index: LibraryIndexRepository | None = None,
    organize_plan: OrganizePlanRepository | None = None,
) -> Callable[[ApplyInput, ApplyProgressCallback | None, Event], ApplyResult]:
    """FileRepository와 OperationLog 팩토리가 주입된 적용 실행 함수를 만든다.

    Args:
        file_repo: 파일 이동 포트.
        operation_log_factory: log_root Path로 OperationLogRepository를 만드는 함수.
        library_index: 적용 후 인덱스 경로 갱신. None이면 생략.
        organize_plan: 플랜·아이템 상태 갱신. None이면 생략.

    Returns:
        (ApplyInput, progress_callback, cancel_token) -> ApplyResult 클로저.
    """

    def execute(
        input_dto: ApplyInput,
        progress_callback: ApplyProgressCallback | None,
        cancel_token: Event,
    ) -> ApplyResult:
        """계획을 적용한다.

        Args:
            input_dto: 작업 목록·dry_run·로그 루트·선택적 소스 루트(빈 폴더 정리).
            progress_callback: ProgressEvent 콜백.
            cancel_token: 취소 시 중단.

        Returns:
            로그 경로·이동 건수·오류 메시지.
        """
        ops = list(input_dto.operations)
        if not ops:
            return ApplyResult(log_path=None, moved_count=0, error="적용할 작업이 없습니다.")

        log_root = (input_dto.log_root or "").strip()
        if not log_root:
            return ApplyResult(
                log_path=None, moved_count=0, error="로그 루트 경로가 비어 있습니다."
            )

        plan_id = input_dto.organize_plan_id
        item_ids = list(input_dto.organize_item_ids)
        root_idx = input_dto.index_root_id

        op_log = operation_log_factory(Path(log_root))
        try:
            log_path = op_log.save_plan(cast(list[object], ops))
        except OSError as e:
            return ApplyResult(log_path=None, moved_count=0, error=str(e))

        if input_dto.dry_run:
            return ApplyResult(log_path=log_path, moved_count=0)

        if organize_plan is not None and plan_id is not None:
            organize_plan.set_plan_fs_log_path(
                plan_id,
                str(log_path) if log_path is not None else None,
            )

        total = len(ops)
        moved = 0
        for i, op in enumerate(ops):
            if cancel_token.is_set():
                if organize_plan is not None and plan_id is not None:
                    organize_plan.update_plan_status(plan_id, "failed")
                return ApplyResult(
                    log_path=log_path,
                    moved_count=moved,
                    error="취소되었습니다.",
                )
            dest = Path(op.destination_path)
            src = Path(op.source_path)
            src_path_str = str(src)
            dest_path_str = str(dest)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                file_repo.move(src, dest)
            except OSError as e:
                if organize_plan is not None and plan_id is not None:
                    if i < len(item_ids):
                        organize_plan.update_item_status(item_ids[i], "failed")
                    organize_plan.update_plan_status(plan_id, "failed")
                return ApplyResult(
                    log_path=log_path,
                    moved_count=moved,
                    error=str(e),
                )
            moved += 1
            if library_index is not None and root_idx is not None:
                library_index.relocate_media_file(
                    root_idx,
                    old_absolute_path=src_path_str,
                    new_absolute_path=dest_path_str,
                )
            if organize_plan is not None and plan_id is not None and i < len(item_ids):
                organize_plan.update_item_status(item_ids[i], "applied")
            if progress_callback is not None:
                cur = i + 1
                progress_callback(
                    ProgressEvent(
                        stage="apply",
                        current=cur,
                        total=total,
                        message=f"파일 이동 중 ({cur}/{total})",
                        percent=int(100 * cur / total),
                        item_path=dest_path_str,
                    )
                )

        if organize_plan is not None and plan_id is not None:
            organize_plan.update_plan_status(plan_id, "applied")

        source_root = (input_dto.source_root or "").strip()
        if source_root:
            file_repo.prune_empty_dirs_under(Path(source_root))

        return ApplyResult(log_path=log_path, moved_count=moved)

    return execute
