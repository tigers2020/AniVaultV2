"""Pipeline result panel UI state helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from anivault.constants.gui.navigation import LEGACY_VIEW_KEY_MAP, VIEW_DETAILS, VIEW_TO_INDEX
from anivault.interfaces.gui.settings_storage import load_all, save_all


class PipelineResultUiState(TypedDict):
    """Persisted UI state payload for PipelineResultPanel."""

    view_key: str
    details_pane: bool
    preview_pane: bool
    selected_index: int


DEFAULT_UI_STATE: PipelineResultUiState = {
    "view_key": VIEW_DETAILS,
    "details_pane": False,
    "preview_pane": False,
    "selected_index": -1,
}


def normalize_pipeline_ui_state(data: dict[str, object]) -> PipelineResultUiState:
    view_key = data.get("view_key")
    details_pane = data.get("details_pane")
    preview_pane = data.get("preview_pane")
    selected_index = data.get("selected_index")
    normalized: PipelineResultUiState = {
        "view_key": DEFAULT_UI_STATE["view_key"],
        "details_pane": DEFAULT_UI_STATE["details_pane"],
        "preview_pane": DEFAULT_UI_STATE["preview_pane"],
        "selected_index": DEFAULT_UI_STATE["selected_index"],
    }
    if isinstance(view_key, str):
        view_key = LEGACY_VIEW_KEY_MAP.get(view_key, view_key)
        if view_key in VIEW_TO_INDEX:
            normalized["view_key"] = view_key
    if isinstance(details_pane, bool):
        normalized["details_pane"] = details_pane
    if isinstance(preview_pane, bool):
        normalized["preview_pane"] = preview_pane
    if isinstance(selected_index, int):
        normalized["selected_index"] = selected_index
    return normalized


def restore_pipeline_result_panel_ui_state(
    normalized: PipelineResultUiState,
    *,
    set_restoring: Callable[[bool], None],
    set_pending_selected_index: Callable[[int], None],
    apply_view_key: Callable[[str], None],
    apply_details_pane: Callable[[bool], None],
    apply_preview_pane: Callable[[bool], None],
) -> None:
    set_restoring(True)
    set_pending_selected_index(normalized["selected_index"])
    apply_view_key(normalized["view_key"])
    apply_details_pane(bool(normalized["details_pane"]))
    apply_preview_pane(bool(normalized["preview_pane"]))
    set_restoring(False)


def load_normalized_pipeline_ui_state_from_settings() -> PipelineResultUiState:
    data = load_all()
    ui_state = data.get("ui_state", {})
    pipeline_results = ui_state.get("pipeline_results", {}) if isinstance(ui_state, dict) else {}
    return normalize_pipeline_ui_state(
        pipeline_results if isinstance(pipeline_results, dict) else {}
    )


def save_pipeline_result_panel_ui_state(
    state: PipelineResultUiState,
) -> None:
    data = load_all()
    ui_state = data.setdefault("ui_state", {})
    if not isinstance(ui_state, dict):
        ui_state = {}
        data["ui_state"] = ui_state
    ui_state["pipeline_results"] = dict(state)
    save_all(data)
