"""State normalization helpers for PipelineResultPanel."""

from anivault.interfaces.gui.components.molecules.view_toggle_bar import VIEW_CONTENT
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel


def test_normalize_ui_state_maps_legacy_tiles_to_content() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    normalized = panel._normalize_ui_state(  # type: ignore[attr-defined]
        {"view_key": "tiles", "details_pane": False, "preview_pane": False, "selected_index": 0}
    )
    assert normalized["view_key"] == VIEW_CONTENT


def test_normalize_ui_state_applies_fallbacks() -> None:
    """Unknown keys/types should be normalized to safe defaults."""
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    normalized = panel._normalize_ui_state(  # type: ignore[attr-defined]
        {
            "view_key": "unknown",
            "details_pane": "yes",
            "preview_pane": "no",
            "selected_index": "bad",
        }
    )
    assert normalized["view_key"] == "details"
    assert normalized["details_pane"] is False
    assert normalized["preview_pane"] is False
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
