"""Helpers for building and merging planning results in the presenter layer."""

from __future__ import annotations

import os
from typing import Any

from anivault.constants.gui.components import PIPELINE_ROW_STATUS_MOVED
from anivault.contracts.planning import PlanInput, PlanResult
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.interfaces.gui.models import (
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_rows_ready_for_plan,
)
from anivault.interfaces.gui.presenters.row_mapper import copy_pipeline_row


def resolve_pipeline_row_poster_url(
    *,
    local_absolute_path: str | None,
    cdn_poster_url: str,
) -> str:
    """Resolve the final poster display URL for a pipeline row."""

    return resolve_final_poster_display_source(local_absolute_path, cdn_poster_url)


def try_build_plan_input_from_settings(
    rows: list[PipelineRow],
    path_rules: dict[str, Any],
    *,
    include_companion_subtitles: bool = True,
    index_root_id: int | None = None,
) -> tuple[PlanInput | None, str | None]:
    """Build a PlanInput from rows plus settings data."""

    if not rows:
        return None, "empty"
    ready_rows = pipeline_rows_ready_for_plan(rows)
    if not ready_rows:
        return None, "no_matched"
    path_template = (str(path_rules.get("path_template") or "")).strip()
    target_root = (str(path_rules.get("target_root") or "")).strip()
    if not path_template or not target_root:
        return None, "path_rules"
    return (
        PlanInput(
            files=tuple(ready_rows),
            path_template=path_template,
            target_root=target_root,
            unknown_resolution=(str(path_rules.get("unknown_resolution") or "Unknown")).strip()
            or "Unknown",
            unknown_group_folder=(
                str(path_rules.get("unknown_group_folder") or "Needs_Review")
            ).strip()
            or "Needs_Review",
            include_companion_subtitles=include_companion_subtitles,
            index_root_id=index_root_id,
        ),
        None,
    )


def _merge_path_key(path: str) -> str:
    try:
        return os.path.normcase(os.path.normpath(path))
    except (TypeError, ValueError):
        return path


def merge_plan_into_pipeline_rows(model: PipelineTableModel, plan: PlanResult) -> None:
    """Reflect applied planning results back into the pipeline table model."""

    source_to_destination = {
        _merge_path_key(operation.source_path): operation.destination_path
        for operation in plan.moves
    }
    merged_rows: list[PipelineRow] = []
    for row in model.flat_rows():
        lookup = _merge_path_key(row.original_file)
        if lookup in source_to_destination:
            merged_rows.append(
                copy_pipeline_row(
                    row,
                    status=PIPELINE_ROW_STATUS_MOVED,
                    target_path=source_to_destination[lookup],
                )
            )
        else:
            merged_rows.append(row)
    model.set_rows(group_pipeline_rows(merged_rows))
