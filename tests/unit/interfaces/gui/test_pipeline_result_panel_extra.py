from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_CONTENT,
    VIEW_DETAILS,
    VIEW_ICON_M,
)
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
)
from anivault.interfaces.gui.templates import pipeline_result_panel as panel_module
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel


def _make_group(path: str, *, matched: bool = True) -> PipelineGroupRow:
    row = PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show" if matched else "",
        tmdb_series_id="1" if matched else "",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="matched" if matched else "parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
    )
    return group_pipeline_rows([row])[0]


def test_apply_list_content_for_view_key_switches_between_rows_and_empty() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._content_view = MagicMock()  # type: ignore[attr-defined]
    rows = [_make_group("F:/Anime/show01.mkv")]

    panel._apply_list_content_for_view_key(VIEW_CONTENT, rows)  # type: ignore[attr-defined]
    panel._apply_list_content_for_view_key(VIEW_DETAILS, rows)  # type: ignore[attr-defined]

    assert panel._content_view.set_rows.call_args_list[0].args == (rows,)  # type: ignore[attr-defined]
    assert panel._content_view.set_rows.call_args_list[1].args == ([],)  # type: ignore[attr-defined]


def test_on_split_table_selection_ignores_out_of_range_and_maps_valid_selection() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    matched = [_make_group("F:/Anime/show01.mkv")]
    panel._matched_model = SimpleNamespace(rows=lambda: matched)  # type: ignore[attr-defined]
    panel._unmatched_model = SimpleNamespace(rows=lambda: [])  # type: ignore[attr-defined]
    panel._unified_index_for_group = lambda group: 4  # type: ignore[attr-defined]
    panel._apply_unified_selection = MagicMock()  # type: ignore[attr-defined]

    panel._on_split_table_selection("matched", -1)  # type: ignore[attr-defined]
    panel._on_split_table_selection("matched", 0)  # type: ignore[attr-defined]

    panel._apply_unified_selection.assert_called_once_with(4)  # type: ignore[attr-defined]


def test_sync_split_tables_selection_handles_matched_unmatched_and_missing() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    matched_group = _make_group("F:/Anime/show01.mkv")
    unmatched_group = _make_group("F:/Anime/show02.mkv", matched=False)
    panel._rows = [matched_group, unmatched_group]  # type: ignore[attr-defined]
    panel._matched_model = SimpleNamespace(rows=lambda: [matched_group])  # type: ignore[attr-defined]
    panel._unmatched_model = SimpleNamespace(rows=lambda: [unmatched_group])  # type: ignore[attr-defined]
    panel._matched_table = MagicMock()  # type: ignore[attr-defined]
    panel._unmatched_table = MagicMock()  # type: ignore[attr-defined]

    panel._sync_split_tables_selection(0)  # type: ignore[attr-defined]
    panel._sync_split_tables_selection(1)  # type: ignore[attr-defined]
    panel._sync_split_tables_selection(99)  # type: ignore[attr-defined]

    assert panel._matched_table.select_row.call_args_list[0].args == (0,)  # type: ignore[attr-defined]
    assert panel._unmatched_table.select_row.call_args_list[0].args == (-1,)  # type: ignore[attr-defined]
    assert panel._unmatched_table.select_row.call_args_list[1].args == (0,)  # type: ignore[attr-defined]
    assert panel._matched_table.select_row.call_args_list[-1].args == (-1,)  # type: ignore[attr-defined]


def test_apply_unified_selection_updates_details_and_persists() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    group = _make_group("F:/Anime/show01.mkv")
    emitted: list[int] = []
    panel.selection_changed = SimpleNamespace(emit=lambda index: emitted.append(index))  # type: ignore[attr-defined]
    panel._rows = [group]  # type: ignore[attr-defined]
    panel._details_pane = MagicMock()  # type: ignore[attr-defined]
    panel._sync_split_tables_selection = MagicMock()  # type: ignore[attr-defined]
    panel._persist_ui_state = MagicMock()  # type: ignore[attr-defined]

    panel._apply_unified_selection(0)  # type: ignore[attr-defined]
    panel._apply_unified_selection(5)  # type: ignore[attr-defined]

    assert emitted == [0, 5]
    assert panel._details_pane.set_row.call_args_list[0].args == (group,)  # type: ignore[attr-defined]
    assert panel._details_pane.set_row.call_args_list[1].args == (None,)  # type: ignore[attr-defined]


def test_ensure_poster_grid_for_view_key_builds_once_and_reuses_cache() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    grid = MagicMock()
    cached_cards = [SimpleNamespace()]
    grid.cards.return_value = cached_cards
    rows = [_make_group("F:/Anime/show01.mkv")]
    fresh_cards = [SimpleNamespace(), SimpleNamespace()]
    panel._poster_grids = {VIEW_ICON_M: grid}  # type: ignore[attr-defined]
    panel._poster_grid_dirty = {VIEW_ICON_M: True}  # type: ignore[attr-defined]
    panel._make_compact_grid_cards = lambda incoming: fresh_cards if incoming == rows else []  # type: ignore[attr-defined]
    panel._make_card_clickable = MagicMock()  # type: ignore[attr-defined]

    first = panel._ensure_poster_grid_for_view_key(VIEW_ICON_M, rows)  # type: ignore[attr-defined]
    second = panel._ensure_poster_grid_for_view_key(VIEW_ICON_M, rows)  # type: ignore[attr-defined]
    missing = panel._ensure_poster_grid_for_view_key("unknown", rows)  # type: ignore[attr-defined]

    assert first == fresh_cards
    assert second == cached_cards
    assert missing == []
    grid.set_cards.assert_called_once_with(fresh_cards)
    assert panel._make_card_clickable.call_count == 2  # type: ignore[attr-defined]


def test_persist_and_restore_ui_state_round_trip(monkeypatch) -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._restoring_state = False  # type: ignore[attr-defined]
    panel._selected_index = 3  # type: ignore[attr-defined]
    panel._view_bar = SimpleNamespace(  # type: ignore[attr-defined]
        current_view=lambda: VIEW_ICON_M,
    )
    saved: list[dict[str, object]] = []
    monkeypatch.setattr(panel_module, "save_all", lambda payload: saved.append(payload))

    panel._persist_ui_state()  # type: ignore[attr-defined]

    assert saved == [
        {
            "ui_state": {
                "pipeline_results": {
                    "view_key": VIEW_ICON_M,
                    "selected_index": 3,
                }
            }
        }
    ]

    monkeypatch.setattr(
        panel_module,
        "load_all",
        lambda: {
            "ui_state": {
                "pipeline_results": {
                    "view_key": "tiles",
                    "selected_index": 7,
                }
            }
        },
    )
    on_view: list[str] = []
    panel._on_view_changed = lambda key: on_view.append(key)  # type: ignore[attr-defined]

    panel._restore_ui_state()  # type: ignore[attr-defined]

    assert on_view == [VIEW_CONTENT]
    assert panel._pending_selected_index == 7  # type: ignore[attr-defined]
    assert panel._restoring_state is False  # type: ignore[attr-defined]


def test_sync_views_from_model_updates_tables_cards_and_selection() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    matched = PipelineRow(
        original_file="F:/Anime/show01.mkv",
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show",
        tmdb_series_id="1",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="matched",
        poster_url="",
        backdrop_url="",
        target_path="F:/Library/show01.mkv",
    )
    unmatched = PipelineRow(
        original_file="F:/Anime/show02.mkv",
        parsed_title="Show 2",
        parse_group="show-2",
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2025",
        season="1",
        resolution="720p",
        status="parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
    )
    grouped_rows = group_pipeline_rows([matched, unmatched])
    panel._model = SimpleNamespace(  # type: ignore[attr-defined]
        rows=lambda: grouped_rows,
        flat_rows=lambda: [matched, unmatched],
    )
    panel._matched_model = MagicMock()  # type: ignore[attr-defined]
    panel._unmatched_model = MagicMock()  # type: ignore[attr-defined]
    panel._view_bar = SimpleNamespace(current_view=lambda: VIEW_CONTENT)  # type: ignore[attr-defined]
    panel._content_view = SimpleNamespace(poster_cards=lambda: [SimpleNamespace(image_url="cached")])  # type: ignore[attr-defined]
    panel._clear_all_poster_grids = MagicMock()  # type: ignore[attr-defined]
    panel._apply_list_content_for_view_key = MagicMock()  # type: ignore[attr-defined]
    panel._ensure_poster_grid_for_view_key = MagicMock(return_value=[SimpleNamespace(image_url="grid")])  # type: ignore[attr-defined]
    panel._refresh_all_poster_pixmaps = MagicMock()  # type: ignore[attr-defined]
    panel._selectable_index = MagicMock(return_value=1)  # type: ignore[attr-defined]
    panel._on_selection = MagicMock()  # type: ignore[attr-defined]

    panel._sync_views_from_model()  # type: ignore[attr-defined]

    assert panel._rows == grouped_rows  # type: ignore[attr-defined]
    assert panel._matched_model.set_rows.call_count == 1  # type: ignore[attr-defined]
    assert panel._unmatched_model.set_rows.call_count == 1  # type: ignore[attr-defined]
    panel._apply_list_content_for_view_key.assert_called_once_with(VIEW_CONTENT, grouped_rows)  # type: ignore[attr-defined]
    panel._ensure_poster_grid_for_view_key.assert_called_once_with(VIEW_CONTENT, grouped_rows)  # type: ignore[attr-defined]
    panel._on_selection.assert_called_once_with(1)  # type: ignore[attr-defined]


def _ensure_qapp() -> QApplication:
    inst = QApplication.instance()
    return inst if isinstance(inst, QApplication) else QApplication([])


def test_panel_syncs_on_model_data_changed_without_reset(monkeypatch) -> None:
    """TMDB 증분 갱신(update_rows_if_compatible)은 dataChanged만 쏘므로 패널도 구독해야 한다."""
    _ensure_qapp()
    monkeypatch.setattr(panel_module, "load_all", lambda: {})
    monkeypatch.setattr(panel_module, "save_all", lambda _payload: None)

    model = PipelineTableModel()
    panel = PipelineResultPanel(model=model)
    path = "F:/Anime/show01.mkv"
    unmatched = PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
    )
    model.set_rows(group_pipeline_rows([unmatched]))
    QApplication.processEvents()

    assert len(panel._rows) == 1  # type: ignore[attr-defined]
    assert (panel._rows[0].tmdb_korean_title_group or "").strip() == ""  # type: ignore[attr-defined]

    matched = PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="KoreanDisplay",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="matched",
        poster_url="",
        backdrop_url="",
        target_path="",
    )
    updated = group_pipeline_rows([matched])
    assert model.update_rows_if_compatible(updated) is True
    QApplication.processEvents()

    assert (panel._rows[0].tmdb_korean_title_group or "").strip() == "KoreanDisplay"  # type: ignore[attr-defined]
