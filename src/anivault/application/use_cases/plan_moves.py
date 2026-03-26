"""plan_moves.py

매칭된 파일로부터 이동 계획을 구성한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Event

from anivault.application.dto.match_result import MatchFileRow
from anivault.application.dto.plan import (
    PlanInput,
    PlanResult,
    match_file_row_to_path_template_input,
)
from anivault.application.dto.progress import ProgressEvent
from anivault.domain.models import FileOperation, OperationType
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
        row: 매칭 파일 행.
        tpl: path_template.
        target_root: Target root.
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
    if include_companion_subtitles:
        moves.extend(companion_subtitle_operations(row.original_file, dest))


def make_execute() -> Callable[[PlanInput, PlanProgressCallback | None, Event], PlanResult]:
    """이동 계획 실행 함수를 만든다.

    Args:
        없음.

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
        tpl = input_dto.path_template
        unk_res = input_dto.unknown_resolution
        unk_grp = input_dto.unknown_group_folder

        for i, row in enumerate(files):
            if cancel_token.is_set():
                return PlanResult(moves=tuple(moves))
            _append_primary_and_optional_companion_moves(
                moves,
                row,
                tpl=tpl,
                target_root=target_root,
                unk_res=unk_res,
                unk_grp=unk_grp,
                include_companion_subtitles=input_dto.include_companion_subtitles,
            )
            if progress_callback is not None and total > 0:
                cur = i + 1
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

        return PlanResult(moves=tuple(moves))

    return execute
