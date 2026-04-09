"""State normalization helpers for PipelineResultPanel."""

from unittest.mock import MagicMock

from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_CONTENT,
    VIEW_DETAILS,
)
from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel


class _FakeFinishedSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class _FakeThread:
    def __init__(self) -> None:
        self.finished = _FakeFinishedSignal()


class _FakePosterCard:
    def __init__(self, image_url: str) -> None:
        self.image_url = image_url
        self.pixmap = None

    def set_pixmap(self, pixmap) -> None:
        self.pixmap = pixmap


def test_normalize_ui_state_maps_legacy_tiles_to_content() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    normalized = panel._normalize_ui_state(  # type: ignore[attr-defined]
        {"view_key": "tiles", "selected_index": 0}
    )
    assert normalized["view_key"] == VIEW_CONTENT


def test_normalize_ui_state_maps_legacy_list_to_details() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    normalized = panel._normalize_ui_state(  # type: ignore[attr-defined]
        {"view_key": "list", "selected_index": 0}
    )
    assert normalized["view_key"] == VIEW_DETAILS


def test_normalize_ui_state_applies_fallbacks() -> None:
    """Unknown keys/types should be normalized to safe defaults."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    normalized = panel._normalize_ui_state(  # type: ignore[attr-defined]
        {
            "view_key": "unknown",
            "selected_index": "bad",
        }
    )
    assert normalized["view_key"] == "details"
    assert normalized["selected_index"] == -1


def test_selectable_index_prefers_pending_then_current() -> None:
    """Selection index should prioritize pending and clamp to valid range."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._pending_selected_index = 2  # type: ignore[attr-defined]
    panel._selected_index = 1  # type: ignore[attr-defined]

    first = panel._selectable_index(5)  # type: ignore[attr-defined]
    second = panel._selectable_index(5)  # type: ignore[attr-defined]

    assert first == 2
    assert second == 1


def test_selectable_index_returns_zero_or_minus_one_for_out_of_range() -> None:
    """Out-of-range selected index should fall back to first row or empty."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._pending_selected_index = 99  # type: ignore[attr-defined]
    panel._selected_index = 50  # type: ignore[attr-defined]

    non_empty = panel._selectable_index(3)  # type: ignore[attr-defined]
    empty = panel._selectable_index(0)  # type: ignore[attr-defined]

    assert non_empty == 0
    assert empty == -1


def test_icon_grid_same_card_keeps_details_open_and_selects() -> None:
    """동일 행 재클릭이어도 아이콘 모드에서는 상세 패널을 유지한다."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._set_details_pane_visible = MagicMock()  # type: ignore[method-assign]
    selection_calls: list[int] = []
    panel._on_selection = lambda i: selection_calls.append(i)  # type: ignore[method-assign]

    panel._on_icon_grid_card_clicked(2)  # type: ignore[attr-defined]

    panel._set_details_pane_visible.assert_called_once_with(True)
    assert selection_calls == [2]


def test_icon_grid_different_card_opens_selection_without_close() -> None:
    """다른 행이면 세부 창을 켜고(필요 시) 해당 행으로 선택한다."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._set_details_pane_visible = MagicMock()  # type: ignore[method-assign]

    selection_calls: list[int] = []

    def _on_sel(i: int) -> None:
        selection_calls.append(i)

    panel._on_selection = _on_sel  # type: ignore[method-assign]

    panel._on_icon_grid_card_clicked(3)  # type: ignore[attr-defined]

    panel._set_details_pane_visible.assert_called_once_with(True)
    assert selection_calls == [3]


def test_cancel_signal_disconnects_when_thread_finishes() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    dialog = MagicMock()
    worker = MagicMock()
    thread = _FakeThread()
    cancel_slot = worker.cancel

    presenter._disconnect_cancel_on_thread_finished(dialog, cancel_slot, thread)  # type: ignore[attr-defined]
    thread.finished.callback()

    dialog.canceled.disconnect.assert_called_once_with(cancel_slot)


def test_refresh_all_poster_pixmaps_loads_local_paths() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    image_loader = MagicMock()
    image_loader.get.return_value = None
    panel._image_loader = image_loader  # type: ignore[attr-defined]
    panel._cards_by_url = {}  # type: ignore[attr-defined]
    card = _FakePosterCard("F:\\cache\\poster.jpg")

    panel._refresh_all_poster_pixmaps([card])  # type: ignore[arg-type, attr-defined]

    image_loader.get.assert_called_once_with("F:\\cache\\poster.jpg")
    image_loader.load.assert_called_once_with("F:\\cache\\poster.jpg")
    assert panel._cards_by_url == {"F:\\cache\\poster.jpg": [card]}  # type: ignore[attr-defined]
