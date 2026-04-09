"""plan_moves.py

Plan move operations from matched rows.

Author: Pom Kim
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import cast

from anivault.application.dto.match_result import MatchFileRow
from anivault.application.dto.organize_plan import (
    OrganizeOperationKind,
    OrganizePlanAppendRow,
    OrganizePlanStatus,
)
from anivault.application.dto.plan import (
    PlanInput,
    PlanMovePreviewMeta,
    PlanResult,
    match_file_row_group_key,
    match_file_row_group_label,
    match_file_row_to_path_template_input,
)
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.organize_plan_port import OrganizePlanRepository
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_PLAN
from anivault.constants.application.statuses import (
    ORGANIZE_OPERATION_KIND_MOVE,
    ORGANIZE_PLAN_STATUS_PREVIEWED,
)
from anivault.constants.domain.media import MEDIA_KIND_SUBTITLE, MEDIA_KIND_VIDEO
from anivault.domain.models import FileOperation, OperationType
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.services.companion_subtitles import companion_subtitle_operations
from anivault.domain.services.path_template import (
    effective_resolution_segment,
    render_destination_path,
)

PlanProgressCallback = Callable[[ProgressEvent], None]


def _plan_input_error_message(input_dto: PlanInput) -> str | None:
    """Return a user-facing validation error when planning cannot proceed."""
    target_root = (input_dto.target_root or "").strip()
    if not target_root:
        return "Settings > Path Rules에서 Target root folder를 지정해 주세요."

    files = list(input_dto.files)
    if len(files) == 0:
        return "계획할 파일이 없습니다."

    for row in files:
        if not (row.tmdb_korean_title_group or "").strip():
            return "TMDB 시리즈 제목 그룹이 비어 있는 항목이 있습니다. 매칭을 완료한 뒤 다시 시도해 주세요."

    return None


def _append_primary_and_optional_companion_moves(
    moves: list[FileOperation],
    move_kinds: list[str],
    move_preview: list[PlanMovePreviewMeta],
    row: MatchFileRow,
    *,
    tpl: str,
    target_root: str,
    unk_res: str,
    unk_grp: str,
    include_companion_subtitles: bool,
    dir_listing_cache: dict[Path, list[Path]] | None,
) -> None:
    """Append the main move and optional companion subtitle moves for one row."""
    pti = match_file_row_to_path_template_input(row)
    dest = render_destination_path(
        tpl,
        pti,
        target_root=target_root,
        unknown_resolution=unk_res,
        unknown_group_folder=unk_grp,
    )
    preview_meta = PlanMovePreviewMeta(
        group_key=match_file_row_group_key(row),
        group_label=match_file_row_group_label(row),
        resolution_segment=effective_resolution_segment(row.resolution, unk_res),
    )
    moves.append(
        FileOperation(
            operation_type=OperationType.MOVE,
            source_path=row.original_file,
            destination_path=dest,
        )
    )
    move_kinds.append(MEDIA_KIND_VIDEO)
    move_preview.append(preview_meta)
    if include_companion_subtitles:
        entries_kw: list[Path] | None = None
        if dir_listing_cache is not None:
            parent = Path(row.original_file).parent
            if parent not in dir_listing_cache:
                try:
                    dir_listing_cache[parent] = list(parent.iterdir())
                except OSError:
                    dir_listing_cache[parent] = []
            entries_kw = dir_listing_cache[parent]
        for op in companion_subtitle_operations(
            row.original_file,
            dest,
            directory_entries=entries_kw,
        ):
            moves.append(op)
            move_kinds.append(MEDIA_KIND_SUBTITLE)
            move_preview.append(preview_meta)


def _emit_plan_progress(
    progress_callback: PlanProgressCallback | None,
    *,
    index: int,
    total: int,
    row: MatchFileRow,
) -> None:
    """Emit progress updates while planning."""
    if progress_callback is None or total <= 0:
        return
    cur = index + 1
    progress_callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_PLAN,
            current=cur,
            total=total,
            message=f"경로 계획 중 ({cur}/{total})",
            percent=int(PROGRESS_PERCENT_MAX * cur / total),
            item_path=row.original_file,
        )
    )


def _throttled_plan_progress(
    progress_callback: PlanProgressCallback | None,
    *,
    index: int,
    total: int,
    row: MatchFileRow,
    last_emitted_percent: int,
) -> int:
    """Emit plan progress when first, last, or integer percent increases; return new last percent."""
    if progress_callback is None or total <= 0:
        return last_emitted_percent
    cur = index + 1
    pct = int(PROGRESS_PERCENT_MAX * cur / total)
    if index != 0 and index != total - 1 and pct <= last_emitted_percent:
        return last_emitted_percent
    _emit_plan_progress(progress_callback, index=index, total=total, row=row)
    return pct


def _persist_plan_if_needed(
    *,
    organize_plan: OrganizePlanRepository | None,
    input_dto: PlanInput,
    files: list[MatchFileRow],
    moves: list[FileOperation],
    move_kinds: list[str],
    move_preview: list[PlanMovePreviewMeta],
) -> PlanResult | None:
    """Persist the preview plan when the organize-plan repository is available."""
    if organize_plan is None or input_dto.index_root_id is None or not moves:
        return None
    if len(move_kinds) != len(moves):
        return PlanResult(
            moves=tuple(moves),
            move_preview=tuple(move_preview),
            error="내부 오류: 이동 작업과 종류 수가 일치하지 않습니다.",
        )
    if len(move_preview) != len(moves):
        return PlanResult(
            moves=tuple(moves),
            move_preview=tuple(move_preview),
            error="내부 오류: Dry Run 메타 수가 이동 작업과 일치하지 않습니다.",
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
            cast(OrganizePlanStatus, ORGANIZE_PLAN_STATUS_PREVIEWED),
            summary,
        )
        rows = tuple(
            OrganizePlanAppendRow(
                src_path_norm=normalize_path_key(m.source_path),
                dst_path_norm=normalize_path_key(m.destination_path),
                operation_kind=cast(OrganizeOperationKind, ORGANIZE_OPERATION_KIND_MOVE),
                detail_json=json.dumps({"kind": kind}, ensure_ascii=False),
            )
            for m, kind in zip(moves, move_kinds, strict=True)
        )
        item_ids = organize_plan.append_items(plan_id, rows)
    except (OSError, sqlite3.Error) as e:
        return PlanResult(moves=tuple(moves), move_preview=tuple(move_preview), error=str(e))
    return PlanResult(
        moves=tuple(moves),
        move_preview=tuple(move_preview),
        organize_plan_id=plan_id,
        organize_item_ids=tuple(item_ids),
    )


def make_execute(
    organize_plan: OrganizePlanRepository | None = None,
) -> Callable[[PlanInput, PlanProgressCallback | None, Event], PlanResult]:
    """Create the plan-moves use case callable."""

    def execute(
        input_dto: PlanInput,
        progress_callback: PlanProgressCallback | None,
        cancel_token: Event,
    ) -> PlanResult:
        """Build move operations from matched rows and path rules."""
        err = _plan_input_error_message(input_dto)
        if err is not None:
            return PlanResult(error=err)

        files = list(input_dto.files)
        total = len(files)
        target_root = (input_dto.target_root or "").strip()

        moves: list[FileOperation] = []
        move_kinds: list[str] = []
        move_preview: list[PlanMovePreviewMeta] = []
        tpl = input_dto.path_template
        unk_res = input_dto.unknown_resolution
        unk_grp = input_dto.unknown_group_folder
        dir_listing_cache: dict[Path, list[Path]] | None = (
            {} if input_dto.include_companion_subtitles else None
        )
        last_plan_progress_percent = -1

        for i, row in enumerate(files):
            if cancel_token.is_set():
                return PlanResult(moves=tuple(moves), move_preview=tuple(move_preview))
            _append_primary_and_optional_companion_moves(
                moves,
                move_kinds,
                move_preview,
                row,
                tpl=tpl,
                target_root=target_root,
                unk_res=unk_res,
                unk_grp=unk_grp,
                include_companion_subtitles=input_dto.include_companion_subtitles,
                dir_listing_cache=dir_listing_cache,
            )
            last_plan_progress_percent = _throttled_plan_progress(
                progress_callback,
                index=i,
                total=total,
                row=row,
                last_emitted_percent=last_plan_progress_percent,
            )

        result = PlanResult(moves=tuple(moves), move_preview=tuple(move_preview))
        persisted = _persist_plan_if_needed(
            organize_plan=organize_plan,
            input_dto=input_dto,
            files=files,
            moves=moves,
            move_kinds=move_kinds,
            move_preview=move_preview,
        )
        if persisted is None:
            return result
        return persisted

    return execute
