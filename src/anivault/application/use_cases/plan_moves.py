"""plan_moves.py

매칭된 파일로부터 이동 계획을 구성한다.

Author: Pom Kim
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from threading import Event

from anivault.application.dto.match_result import MatchFileRow
from anivault.application.dto.organize_plan import OrganizePlanAppendRow
from anivault.application.dto.plan import (
    PlanInput,
    PlanResult,
    match_file_row_to_path_template_input,
)
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.organize_plan_port import OrganizePlanRepository
from anivault.domain.models import FileOperation, OperationType
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.services.companion_subtitles import companion_subtitle_operations
from anivault.domain.services.path_template import render_destination_path

PlanProgressCallback = Callable[[ProgressEvent], None]


def _plan_input_error_message(input_dto: PlanInput) -> str | None:
    """플랜 입력이 유효하지 않으면 오류 메시지를, 아니면 None 을 반환한다.

    Args:
        input_dto: 이동 계획 입력.

    Returns:
        오류 메시지 또는 None.
    """
    target_root = (input_dto.target_root or "").strip()
    if not target_root:
        return "Settings → Path Rules에서 Target root folder를 지정하세요."

    files = list(input_dto.files)
    if len(files) == 0:
        return "계획할 파일이 없습니다."

    for row in files:
        if not (row.tmdb_korean_title_group or "").strip():
            return (
                "TMDB 한글 제목 그룹이 비어 있는 행이 있습니다. 매칭을 완료한 뒤 다시 시도하세요."
            )

    return None


def _append_primary_and_optional_companion_moves(
    moves: list[FileOperation],
    move_kinds: list[str],
    row: MatchFileRow,
    *,
    tpl: str,
    target_root: str,
    unk_res: str,
    unk_grp: str,
    include_companion_subtitles: bool,
) -> None:
    """한 매칭 행에 대해 주 파일 이동과(선택) 동반 자막 이동을 moves 에 추가한다.

    Args:
        moves: 누적 작업 목록.
        move_kinds: moves 와 동일 길이로 `video`/`subtitle` 를 쌓는다.
        row: 매칭 파일 행.
        tpl: path_template.
        target_root: Target root 경로.
        unk_res: 미지정 해상도 폴더명.
        unk_grp: 미지정 그룹 폴더명.
        include_companion_subtitles: True면 비디오 옆 같은 stem 자막도 이동.

    Returns:
        None.
    """
    pti = match_file_row_to_path_template_input(row)
    dest = render_destination_path(
        tpl,
        pti,
        target_root=target_root,
        unknown_resolution=unk_res,
        unknown_group_folder=unk_grp,
    )
    moves.append(
        FileOperation(
            operation_type=OperationType.MOVE,
            source_path=row.original_file,
            destination_path=dest,
        )
    )
    move_kinds.append("video")
    if include_companion_subtitles:
        for op in companion_subtitle_operations(row.original_file, dest):
            moves.append(op)
            move_kinds.append("subtitle")


def _emit_plan_progress(
    progress_callback: PlanProgressCallback | None,
    *,
    index: int,
    total: int,
    row: MatchFileRow,
) -> None:
    """계획 진행률 이벤트를 조건부로 발행한다."""
    if progress_callback is None or total <= 0:
        return
    cur = index + 1
    progress_callback(
        ProgressEvent(
            stage="plan",
            current=cur,
            total=total,
            message=f"경로 계획 중 ({cur}/{total})",
            percent=int(100 * cur / total),
            item_path=row.original_file,
        )
    )


def _persist_plan_if_needed(
    *,
    organize_plan: OrganizePlanRepository | None,
    input_dto: PlanInput,
    files: list[MatchFileRow],
    moves: list[FileOperation],
    move_kinds: list[str],
) -> PlanResult | None:
    """필요한 경우 계획을 저장소에 기록하고 결과를 반환한다.

    Returns:
        저장을 생략하면 None, 저장 성공/실패 시 해당 PlanResult.
    """
    if organize_plan is None or input_dto.index_root_id is None or not moves:
        return None
    if len(move_kinds) != len(moves):
        return PlanResult(
            moves=tuple(moves),
            error="내부 오류: 이동 작업과 종류 수가 일치하지 않습니다.",
        )
    try:
        summary = json.dumps(
            {
                "v": 1,
                "matched_files": len(files),
                "operations": len(moves),
            },
            ensure_ascii=False,
        )
        plan_id = organize_plan.create_plan(
            input_dto.index_root_id,
            "previewed",
            summary,
        )
        rows = tuple(
            OrganizePlanAppendRow(
                src_path_norm=normalize_path_key(m.source_path),
                dst_path_norm=normalize_path_key(m.destination_path),
                operation_kind="move",
                detail_json=json.dumps({"kind": kind}, ensure_ascii=False),
            )
            for m, kind in zip(moves, move_kinds, strict=True)
        )
        item_ids = organize_plan.append_items(plan_id, rows)
    except (OSError, sqlite3.Error) as e:
        return PlanResult(moves=tuple(moves), error=str(e))
    return PlanResult(
        moves=tuple(moves),
        organize_plan_id=plan_id,
        organize_item_ids=tuple(item_ids),
    )


def make_execute(
    organize_plan: OrganizePlanRepository | None = None,
) -> Callable[[PlanInput, PlanProgressCallback | None, Event], PlanResult]:
    """이동 계획 실행 함수를 만든다.

    Args:
        organize_plan: 플랜 영속화 저장소. None이면 DB에 저장하지 않는다.

    Returns:
        (PlanInput, progress_callback, cancel_token) -> PlanResult 클로저.
    """

    def execute(
        input_dto: PlanInput,
        progress_callback: PlanProgressCallback | None,
        cancel_token: Event,
    ) -> PlanResult:
        """이동 계획을 생성한다.

        Args:
            input_dto: 매칭 행과 path_rules 값.
            progress_callback: ProgressEvent를 받는 콜백. None이면 생략.
            cancel_token: 설정 시 중단.

        Returns:
            계획 결과. 검증 실패 시 error에 메시지.
        """
        err = _plan_input_error_message(input_dto)
        if err is not None:
            return PlanResult(error=err)

        files = list(input_dto.files)
        total = len(files)
        target_root = (input_dto.target_root or "").strip()

        moves: list[FileOperation] = []
        move_kinds: list[str] = []
        tpl = input_dto.path_template
        unk_res = input_dto.unknown_resolution
        unk_grp = input_dto.unknown_group_folder

        for i, row in enumerate(files):
            if cancel_token.is_set():
                return PlanResult(moves=tuple(moves))
            _append_primary_and_optional_companion_moves(
                moves,
                move_kinds,
                row,
                tpl=tpl,
                target_root=target_root,
                unk_res=unk_res,
                unk_grp=unk_grp,
                include_companion_subtitles=input_dto.include_companion_subtitles,
            )
            _emit_plan_progress(progress_callback, index=i, total=total, row=row)

        result = PlanResult(moves=tuple(moves))
        persisted = _persist_plan_if_needed(
            organize_plan=organize_plan,
            input_dto=input_dto,
            files=files,
            moves=moves,
            move_kinds=move_kinds,
        )
        if persisted is None:
            return result
        return persisted

    return execute
