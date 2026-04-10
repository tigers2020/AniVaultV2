"""State helpers for :class:`PipelineResultPanel`."""

from __future__ import annotations

from typing import TypedDict, cast

from anivault.constants.gui.navigation import LEGACY_VIEW_KEY_MAP, VIEW_TO_INDEX
from anivault.constants.gui.settings import (
    default_pipeline_results,
    pipeline_results_from_loaded,
)
from anivault.interfaces.gui.settings_storage import load_all, save_all


class PipelineResultUiState(TypedDict):
    """Persisted UI state payload for PipelineResultPanel."""

    view_key: str
    selected_index: int


DEFAULT_UI_STATE: PipelineResultUiState = cast(PipelineResultUiState, default_pipeline_results())


def normalize_ui_state(data: dict[str, object]) -> PipelineResultUiState:
    """Normalize raw persisted state into a validated payload."""

    view_key = data.get("view_key")
    selected_index = data.get("selected_index")
    normalized: PipelineResultUiState = {
        "view_key": DEFAULT_UI_STATE["view_key"],
        "selected_index": DEFAULT_UI_STATE["selected_index"],
    }
    if isinstance(view_key, str):
        view_key = LEGACY_VIEW_KEY_MAP.get(view_key, view_key)
        if view_key in VIEW_TO_INDEX:
            normalized["view_key"] = view_key
    if isinstance(selected_index, int):
        normalized["selected_index"] = selected_index
    return normalized


def load_ui_state() -> PipelineResultUiState:
    """Load and normalize persisted pipeline-result UI state."""

    ui_state = load_all().get("ui_state", {})
    pipeline_state: dict[str, object] = {}
    if isinstance(ui_state, dict):
        pipeline_state = {"ui_state": ui_state}
    return normalize_ui_state(pipeline_results_from_loaded(pipeline_state))


def persist_ui_state(*, view_key: str, selected_index: int) -> None:
    """Persist the current pipeline-result UI state."""

    save_all(
        {
            "ui_state": {
                "pipeline_results": {
                    "view_key": view_key,
                    "selected_index": selected_index,
                }
            }
        }
    )


def resolve_selected_index(
    *,
    length: int,
    pending_selected_index: int,
    selected_index: int,
) -> tuple[int, int]:
    """Return the best selectable index and the next pending-selection value."""

    if length <= 0:
        return -1, pending_selected_index
    if 0 <= pending_selected_index < length:
        return pending_selected_index, -1
    if 0 <= selected_index < length:
        return selected_index, pending_selected_index
    return 0, pending_selected_index
