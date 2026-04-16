"""apply_plan.py

계획을 로그에 저장한 뒤 dry_run이 아니면 파일을 이동한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import Final

from anivault.application.ports.file_repository import FileRepository
from anivault.application.ports.library_index_port import LibraryIndexRepository
from anivault.application.ports.operation_log_port import OperationLogRepository
from anivault.application.ports.organize_plan_port import OrganizePlanRepository
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_APPLY
from anivault.contracts.organize_plan import OrganizePlanItemStatus, OrganizePlanStatus
from anivault.contracts.planning import ApplyInput, ApplyResult
from anivault.contracts.progress import ProgressEvent
from anivault.domain.models import FileOperation

ApplyProgressCallback = Callable[[ProgressEvent], None]
FAILED_PLAN_STATUS: Final[OrganizePlanStatus] = "failed"
APPLIED_PLAN_STATUS: Final[OrganizePlanStatus] = "applied"
FAILED_ITEM_STATUS: Final[OrganizePlanItemStatus] = "failed"
APPLIED_ITEM_STATUS: Final[OrganizePlanItemStatus] = "applied"


def _get_operations_or_error(input_dto: ApplyInput) -> ApplyResult | None:
    ops = list(input_dto.operations)
    if not ops:
        return ApplyResult(log_path=None, moved_count=0, error="적용할 작업이 없습니다.")
    return None


def _save_plan_log_or_error(
    operation_log_factory: Callable[[], OperationLogRepository],
    ops: list[FileOperation],
) -> tuple[Path | None, ApplyResult | None]:
    op_log = operation_log_factory()
    try:
        serializable_ops: list[object] = list(ops)
        log_path = op_log.save_plan(serializable_ops)
    except OSError as e:
        return None, ApplyResult(log_path=None, moved_count=0, error=str(e))
    return log_path, None


def _mark_plan_failed_if_needed(
    organize_plan: OrganizePlanRepository | None,
    plan_id: int | None,
) -> None:
    if organize_plan is not None and plan_id is not None:
        organize_plan.update_plan_status(plan_id, FAILED_PLAN_STATUS)


def _mark_item_failed_if_needed(
    organize_plan: OrganizePlanRepository | None,
    item_ids: list[int],
    index: int,
) -> None:
    if organize_plan is not None and index < len(item_ids):
        organize_plan.update_item_status(item_ids[index], FAILED_ITEM_STATUS)


def _mark_item_applied_if_needed(
    organize_plan: OrganizePlanRepository | None,
    item_ids: list[int],
    index: int,
) -> None:
    if organize_plan is not None and index < len(item_ids):
        organize_plan.update_item_status(item_ids[index], APPLIED_ITEM_STATUS)


def _emit_apply_progress_if_needed(
    progress_callback: ApplyProgressCallback | None,
    current_index: int,
    total: int,
    item_path: str,
) -> None:
    if progress_callback is None:
        return
    cur = current_index + 1
    progress_callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_APPLY,
            current=cur,
            total=total,
            message=f"파일 이동 중 ({cur}/{total})",
            percent=int(PROGRESS_PERCENT_MAX * cur / total),
            item_path=item_path,
        )
    )


def _move_operation_or_error(
    file_repo: FileRepository,
    library_index: LibraryIndexRepository | None,
    root_idx: int | None,
    op: FileOperation,
) -> tuple[tuple[str, str] | None, str | None]:
    src = Path(op.source_path)
    dest = Path(op.destination_path)
    src_path_str = str(src)
    dest_path_str = str(dest)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        file_repo.move(src, dest)
    except OSError as e:
        return None, str(e)
    if library_index is not None and root_idx is not None:
        library_index.relocate_media_file(
            root_idx,
            old_absolute_path=src_path_str,
            new_absolute_path=dest_path_str,
        )
    return (src_path_str, dest_path_str), None


def _apply_operations_or_error(
    *,
    ops: list[FileOperation],
    file_repo: FileRepository,
    library_index: LibraryIndexRepository | None,
    root_idx: int | None,
    organize_plan: OrganizePlanRepository | None,
    plan_id: int | None,
    item_ids: list[int],
    progress_callback: ApplyProgressCallback | None,
    cancel_token: Event,
    log_path: Path | None,
) -> ApplyResult | None:
    total = len(ops)
    moved = 0
    for i, op in enumerate(ops):
        if cancel_token.is_set():
            _mark_plan_failed_if_needed(organize_plan, plan_id)
            return ApplyResult(log_path=log_path, moved_count=moved, error="취소되었습니다.")
        moved_paths, move_error = _move_operation_or_error(
            file_repo=file_repo,
            library_index=library_index,
            root_idx=root_idx,
            op=op,
        )
        if move_error is not None:
            if organize_plan is not None and plan_id is not None:
                _mark_item_failed_if_needed(organize_plan, item_ids, i)
                _mark_plan_failed_if_needed(organize_plan, plan_id)
            return ApplyResult(log_path=log_path, moved_count=moved, error=move_error)
        if moved_paths is None:
            return ApplyResult(
                log_path=log_path, moved_count=moved, error="파일 이동 결과가 비어 있습니다."
            )
        moved += 1
        _mark_item_applied_if_needed(organize_plan, item_ids, i)
        _emit_apply_progress_if_needed(progress_callback, i, total, moved_paths[1])
    return ApplyResult(log_path=log_path, moved_count=moved)


def _execute_apply(
    input_dto: ApplyInput,
    progress_callback: ApplyProgressCallback | None,
    cancel_token: Event,
    *,
    file_repo: FileRepository,
    operation_log_factory: Callable[[], OperationLogRepository],
    library_index: LibraryIndexRepository | None = None,
    organize_plan: OrganizePlanRepository | None = None,
) -> ApplyResult:
    ops_error = _get_operations_or_error(input_dto)
    if ops_error is not None:
        return ops_error

    ops = list(input_dto.operations)
    plan_id = input_dto.organize_plan_id
    item_ids = list(input_dto.organize_item_ids)
    root_idx = input_dto.index_root_id

    log_path, log_error = _save_plan_log_or_error(operation_log_factory, ops)
    if log_error is not None:
        return log_error

    if input_dto.dry_run:
        return ApplyResult(log_path=log_path, moved_count=0)

    if organize_plan is not None and plan_id is not None:
        organize_plan.set_plan_fs_log_path(
            plan_id,
            str(log_path) if log_path is not None else None,
        )

    apply_result = _apply_operations_or_error(
        ops=ops,
        file_repo=file_repo,
        library_index=library_index,
        root_idx=root_idx,
        organize_plan=organize_plan,
        plan_id=plan_id,
        item_ids=item_ids,
        progress_callback=progress_callback,
        cancel_token=cancel_token,
        log_path=log_path,
    )
    if apply_result is None:
        return ApplyResult(log_path=log_path, moved_count=0, error="적용 실패")
    if apply_result.error is not None:
        return apply_result

    if organize_plan is not None and plan_id is not None:
        organize_plan.update_plan_status(plan_id, APPLIED_PLAN_STATUS)

    source_root = (input_dto.source_root or "").strip()
    if source_root:
        file_repo.prune_empty_dirs_under(Path(source_root))

    return apply_result


def make_apply_execute(
    file_repo: FileRepository,
    operation_log_factory: Callable[[], OperationLogRepository],
    *,
    library_index: LibraryIndexRepository | None = None,
    organize_plan: OrganizePlanRepository | None = None,
) -> Callable[[ApplyInput, ApplyProgressCallback | None, Event], ApplyResult]:
    """FileRepository와 OperationLog 팩토리가 주입된 적용 실행 함수를 만든다.

    Args:
        file_repo: 파일 이동 포트.
        operation_log_factory: 인자 없이 OperationLogRepository를 만드는 함수.
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
        return _execute_apply(
            input_dto,
            progress_callback,
            cancel_token,
            file_repo=file_repo,
            operation_log_factory=operation_log_factory,
            library_index=library_index,
            organize_plan=organize_plan,
        )

    return execute
