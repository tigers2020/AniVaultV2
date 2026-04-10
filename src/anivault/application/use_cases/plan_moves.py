"""Plan move operations from shared pipeline rows."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import cast

from anivault.application.ports.organize_plan_port import OrganizePlanRepository
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_PLAN
from anivault.constants.application.statuses import (
    ORGANIZE_OPERATION_KIND_MOVE,
    ORGANIZE_PLAN_STATUS_PREVIEWED,
)
from anivault.constants.domain.media import MEDIA_KIND_SUBTITLE, MEDIA_KIND_VIDEO
from anivault.contracts.organize_plan import (
    OrganizeOperationKind,
    OrganizePlanAppendRow,
    OrganizePlanStatus,
)
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.planning import PlanInput, PlanMovePreviewMeta, PlanResult
from anivault.contracts.progress import ProgressEvent
from anivault.domain.models import FileOperation, OperationType, PathTemplateInput
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.pipeline_grouping import pipeline_row_group_key, pipeline_row_group_label
from anivault.domain.services.companion_subtitles import companion_subtitle_operations
from anivault.domain.services.path_template import (
    effective_resolution_segment,
    render_destination_path,
)

PlanProgressCallback = Callable[[ProgressEvent], None]


def _pipeline_row_to_path_template_input(row: PipelineRow) -> PathTemplateInput:
    return PathTemplateInput(
        original_file=row.original_file,
        resolution=row.resolution,
        year=row.year,
        season=row.season,
        korean_title_group=row.tmdb_korean_title_group,
    )


def _plan_input_error_message(input_dto: PlanInput) -> str | None:
    target_root = (input_dto.target_root or "").strip()
    if not target_root:
        return "Settings > Path Rules에서 Target root folder를 지정해 주세요."

    files = list(input_dto.files)
    if not files:
        return "계획할 파일이 없습니다."

    for row in files:
        if not (row.tmdb_korean_title_group or "").strip():
            return "TMDB 시리즈명 그룹이 비어 있는 항목이 있습니다. 매칭을 완료한 뒤 다시 시도해 주세요."

    return None


def _append_primary_and_optional_companion_moves(
    moves: list[FileOperation],
    move_kinds: list[str],
    move_preview: list[PlanMovePreviewMeta],
    row: PipelineRow,
    *,
    tpl: str,
    target_root: str,
    unk_res: str,
    unk_grp: str,
    include_companion_subtitles: bool,
    dir_listing_cache: dict[Path, list[Path]] | None,
) -> None:
    path_template_input = _pipeline_row_to_path_template_input(row)
    destination = render_destination_path(
        tpl,
        path_template_input,
        target_root=target_root,
        unknown_resolution=unk_res,
        unknown_group_folder=unk_grp,
    )
    preview_meta = PlanMovePreviewMeta(
        group_key=pipeline_row_group_key(row),
        group_label=pipeline_row_group_label(row),
        resolution_segment=effective_resolution_segment(row.resolution, unk_res),
    )
    moves.append(
        FileOperation(
            operation_type=OperationType.MOVE,
            source_path=row.original_file,
            destination_path=destination,
        )
    )
    move_kinds.append(MEDIA_KIND_VIDEO)
    move_preview.append(preview_meta)
    if include_companion_subtitles:
        directory_entries: list[Path] | None = None
        if dir_listing_cache is not None:
            parent = Path(row.original_file).parent
            if parent not in dir_listing_cache:
                try:
                    dir_listing_cache[parent] = list(parent.iterdir())
                except OSError:
                    dir_listing_cache[parent] = []
            directory_entries = dir_listing_cache[parent]
        for operation in companion_subtitle_operations(
            row.original_file,
            destination,
            directory_entries=directory_entries,
        ):
            moves.append(operation)
            move_kinds.append(MEDIA_KIND_SUBTITLE)
            move_preview.append(preview_meta)


def _emit_plan_progress(
    progress_callback: PlanProgressCallback | None,
    *,
    index: int,
    total: int,
    row: PipelineRow,
) -> None:
    if progress_callback is None or total <= 0:
        return
    current = index + 1
    progress_callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_PLAN,
            current=current,
            total=total,
            message=f"경로 계획 중 ({current}/{total})",
            percent=int(PROGRESS_PERCENT_MAX * current / total),
            item_path=row.original_file,
        )
    )


def _throttled_plan_progress(
    progress_callback: PlanProgressCallback | None,
    *,
    index: int,
    total: int,
    row: PipelineRow,
    last_emitted_percent: int,
) -> int:
    if progress_callback is None or total <= 0:
        return last_emitted_percent
    current = index + 1
    percent = int(PROGRESS_PERCENT_MAX * current / total)
    if index != 0 and index != total - 1 and percent <= last_emitted_percent:
        return last_emitted_percent
    _emit_plan_progress(progress_callback, index=index, total=total, row=row)
    return percent


def _persist_plan_if_needed(
    *,
    organize_plan: OrganizePlanRepository | None,
    input_dto: PlanInput,
    files: list[PipelineRow],
    moves: list[FileOperation],
    move_kinds: list[str],
    move_preview: list[PlanMovePreviewMeta],
) -> PlanResult | None:
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
            error="내부 오류: Dry Run 메타와 이동 작업 수가 일치하지 않습니다.",
        )
    try:
        summary = json.dumps(
            {"v": 1, "matched_files": len(files), "operations": len(moves)},
            ensure_ascii=False,
        )
        plan_id = organize_plan.create_plan(
            input_dto.index_root_id,
            cast(OrganizePlanStatus, ORGANIZE_PLAN_STATUS_PREVIEWED),
            summary,
        )
        rows = tuple(
            OrganizePlanAppendRow(
                src_path_norm=normalize_path_key(move.source_path),
                dst_path_norm=normalize_path_key(move.destination_path),
                operation_kind=cast(OrganizeOperationKind, ORGANIZE_OPERATION_KIND_MOVE),
                detail_json=json.dumps({"kind": kind}, ensure_ascii=False),
            )
            for move, kind in zip(moves, move_kinds, strict=True)
        )
        item_ids = organize_plan.append_items(plan_id, rows)
    except (OSError, sqlite3.Error) as exc:
        return PlanResult(moves=tuple(moves), move_preview=tuple(move_preview), error=str(exc))
    return PlanResult(
        moves=tuple(moves),
        move_preview=tuple(move_preview),
        organize_plan_id=plan_id,
        organize_item_ids=tuple(item_ids),
    )


def make_execute(
    organize_plan: OrganizePlanRepository | None = None,
) -> Callable[[PlanInput, PlanProgressCallback | None, Event], PlanResult]:
    """Create the planning use case callable."""

    def execute(
        input_dto: PlanInput,
        progress_callback: PlanProgressCallback | None,
        cancel_token: Event,
    ) -> PlanResult:
        error = _plan_input_error_message(input_dto)
        if error is not None:
            return PlanResult(error=error)

        files = list(input_dto.files)
        total = len(files)
        target_root = (input_dto.target_root or "").strip()
        moves: list[FileOperation] = []
        move_kinds: list[str] = []
        move_preview: list[PlanMovePreviewMeta] = []
        directory_listing_cache: dict[Path, list[Path]] | None = (
            {} if input_dto.include_companion_subtitles else None
        )
        last_progress_percent = -1

        for index, row in enumerate(files):
            if cancel_token.is_set():
                return PlanResult(moves=tuple(moves), move_preview=tuple(move_preview))
            _append_primary_and_optional_companion_moves(
                moves,
                move_kinds,
                move_preview,
                row,
                tpl=input_dto.path_template,
                target_root=target_root,
                unk_res=input_dto.unknown_resolution,
                unk_grp=input_dto.unknown_group_folder,
                include_companion_subtitles=input_dto.include_companion_subtitles,
                dir_listing_cache=directory_listing_cache,
            )
            last_progress_percent = _throttled_plan_progress(
                progress_callback,
                index=index,
                total=total,
                row=row,
                last_emitted_percent=last_progress_percent,
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
        return result if persisted is None else persisted

    return execute
