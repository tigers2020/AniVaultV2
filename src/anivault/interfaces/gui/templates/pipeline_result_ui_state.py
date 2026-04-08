"""pipeline_result_ui_state.py

PipelineResultPanel 저장·복원 UI 상태(TypedDict, 정규화, persist 페이로드).

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypedDict

from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_CONTENT,
    VIEW_DETAILS,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_ICON_XL,
)
from anivault.interfaces.gui.settings_storage import load_all, save_all

VIEW_TO_INDEX = {
    VIEW_DETAILS: 0,
    VIEW_CONTENT: 1,
    VIEW_ICON_XL: 2,
    VIEW_ICON_L: 3,
    VIEW_ICON_M: 4,
    VIEW_ICON_S: 5,
}

_LEGACY_VIEW_KEY_MAP = {"tiles": VIEW_CONTENT, "list": VIEW_DETAILS}


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
    """저장된 ui_state 하위 dict를 안전한 기본값이 채워진 형태로 정규화한다.

    Args:
        data: 원시 설정 딕셔너리(pipeline_results 등).

    Returns:
        정규화된 UI 상태.
    """
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
        view_key = _LEGACY_VIEW_KEY_MAP.get(view_key, view_key)
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
    """정규화된 UI 상태를 패널 콜백 순서로 적용한다.

    Args:
        normalized: 설정에서 읽어 정규화한 Pipeline Result UI 상태.
        set_restoring: 복원 구간 시작(True)·종료(False).
        set_pending_selected_index: `modelReset` 직후 선택에 쓸 인덱스.
        apply_view_key: 보기 키 전환(스택·그리드 동기화 등).
        apply_details_pane: 상세 우측 패널 표시 여부.
        apply_preview_pane: 미리보기 우측 패널 표시 여부.

    Returns:
        None.
    """
    set_restoring(True)
    set_pending_selected_index(normalized["selected_index"])
    apply_view_key(normalized["view_key"])
    apply_details_pane(bool(normalized["details_pane"]))
    apply_preview_pane(bool(normalized["preview_pane"]))
    set_restoring(False)


def load_normalized_pipeline_ui_state_from_settings() -> PipelineResultUiState:
    """설정 저장소에서 pipeline_results 블록을 읽어 정규화한다.

    Args:
        없음.

    Returns:
        정규화된 Pipeline Result UI 상태.
    """
    ui_state = load_all().get("ui_state", {})
    pipeline_state: dict[str, object] = {}
    if isinstance(ui_state, dict):
        raw = ui_state.get("pipeline_results", {})
        if isinstance(raw, dict):
            pipeline_state = dict(raw)
    return normalize_pipeline_ui_state(pipeline_state)


def persist_pipeline_results_ui_state(
    *,
    view_key: str,
    details_pane: bool,
    preview_pane: bool,
    selected_index: int,
    skip_if_restoring: bool,
) -> None:
    """Pipeline Result UI 상태를 설정에 기록한다.

    Args:
        view_key: 현재 보기 키.
        details_pane: 상세 패널 표시 여부.
        preview_pane: 미리보기 패널 표시 여부.
        selected_index: 선택된 그룹 인덱스.
        skip_if_restoring: True면 복원 중에는 저장하지 않는다.

    Returns:
        None.
    """
    if skip_if_restoring:
        return
    save_all(
        {
            "ui_state": {
                "pipeline_results": {
                    "view_key": view_key,
                    "details_pane": details_pane,
                    "preview_pane": preview_pane,
                    "selected_index": selected_index,
                }
            }
        }
    )
