from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.interfaces.gui.components.molecules.view_toggle_bar import VIEW_CONTENT, VIEW_ICON_M
from anivault.interfaces.gui.models import PipelineRow, group_pipeline_rows
from anivault.interfaces.gui.templates import pipeline_result_state as panel_state_module
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel


def _group(path: str, *, title: str = "Show", poster_url: str = ""):
    return group_pipeline_rows(
        [
            PipelineRow(
                original_file=path,
                parsed_title=title,
                parse_group=title.lower(),
                tmdb_korean_title_group="",
                tmdb_series_id="",
                tmdb_poster_path="",
                tmdb_backdrop_path="",
                year="2024",
                season="1",
                resolution="1080p",
                status="parsed",
                poster_url=poster_url,
                backdrop_url="",
                target_path="",
            )
        ]
    )[0]


def test_on_view_changed_make_card_clickable_and_clear_grids() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._stack = MagicMock()  # type: ignore[attr-defined]
    panel._view_bar = MagicMock()  # type: ignore[attr-defined]
    panel._model = SimpleNamespace(rows=lambda: [_group("a.mkv")])  # type: ignore[attr-defined]
    panel._apply_list_content_for_view_key = MagicMock()  # type: ignore[attr-defined]
    panel._ensure_poster_grid_for_view_key = MagicMock(return_value=[SimpleNamespace(image_url="a")])  # type: ignore[attr-defined]
    panel._content_view = SimpleNamespace(poster_cards=lambda: [SimpleNamespace(image_url="b")])  # type: ignore[attr-defined]
    panel._set_details_pane_visible = MagicMock()  # type: ignore[attr-defined]
    panel._refresh_all_poster_pixmaps = MagicMock()  # type: ignore[attr-defined]
    panel._persist_ui_state = MagicMock()  # type: ignore[attr-defined]

    panel._on_view_changed(VIEW_ICON_M)  # type: ignore[attr-defined]

    panel._stack.setCurrentIndex.assert_called_once()  # type: ignore[attr-defined]
    panel._view_bar.set_current_view.assert_called_once_with(VIEW_ICON_M)  # type: ignore[attr-defined]
    panel._set_details_pane_visible.assert_called_once_with(True)  # type: ignore[attr-defined]
    panel._refresh_all_poster_pixmaps.assert_called_once()  # type: ignore[attr-defined]

    clicked: list[int] = []
    card = SimpleNamespace(setCursor=MagicMock())
    panel._on_icon_grid_card_clicked = lambda index: clicked.append(index)  # type: ignore[attr-defined]
    panel._make_card_clickable(card, 4)  # type: ignore[attr-defined]
    card.mousePressEvent(None)
    assert clicked == [4]

    grid = MagicMock()
    panel._poster_grids = {"m": grid}  # type: ignore[attr-defined]
    panel._poster_grid_dirty = {"m": False}  # type: ignore[attr-defined]
    panel._clear_all_poster_grids()  # type: ignore[attr-defined]
    grid.set_cards.assert_called_once_with([])
    assert panel._poster_grid_dirty["m"] is True  # type: ignore[attr-defined]


def test_make_compact_grid_cards_and_details_pane_paths() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    monkey_cards: list[dict[str, object]] = []

    def _fake_card(**kwargs):
        monkey_cards.append(kwargs)
        return SimpleNamespace(**kwargs)

    import anivault.interfaces.gui.templates.pipeline_result_panel as panel_module

    original = panel_module.PosterCard
    panel_module.PosterCard = _fake_card
    try:
        cards = panel._make_compact_grid_cards([_group("a.mkv", title="Parsed", poster_url="poster")])  # type: ignore[attr-defined]
    finally:
        panel_module.PosterCard = original

    assert cards and monkey_cards[0]["title"] == "Parsed"

    panel._pane_stack = MagicMock()  # type: ignore[attr-defined]
    panel._main_splitter = SimpleNamespace(width=lambda: 1000, setSizes=MagicMock())  # type: ignore[attr-defined]
    panel._main_min_width = 320  # type: ignore[attr-defined]
    panel._pane_width = 340  # type: ignore[attr-defined]
    panel._persist_ui_state = MagicMock()  # type: ignore[attr-defined]

    panel._set_details_pane_visible(True)  # type: ignore[attr-defined]
    panel._set_details_pane_visible(False)  # type: ignore[attr-defined]

    assert panel._pane_stack.setCurrentIndex.call_count == 2  # type: ignore[attr-defined]


def test_refresh_poster_pixmaps_and_header_height() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._cards_by_url = {}  # type: ignore[attr-defined]
    panel._image_loader = SimpleNamespace(get=lambda url: "pix" if url == "cached" else None, load=MagicMock())  # type: ignore[attr-defined]
    cached = SimpleNamespace(image_url="cached", set_pixmap=MagicMock())
    remote = SimpleNamespace(image_url="remote", set_pixmap=MagicMock())

    panel._refresh_all_poster_pixmaps([cached, remote])  # type: ignore[attr-defined]

    cached.set_pixmap.assert_called_once_with("pix")
    panel._image_loader.load.assert_called_once_with("remote")  # type: ignore[attr-defined]

    panel._header = SimpleNamespace(sizeHint=lambda: SimpleNamespace(height=lambda: 42), setFixedHeight=MagicMock())  # type: ignore[attr-defined]
    panel._sync_header_height()  # type: ignore[attr-defined]
    panel._header.setFixedHeight.assert_called_once_with(42)  # type: ignore[attr-defined]


def test_sync_views_from_model_empty_branch() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._model = SimpleNamespace(rows=lambda: [], flat_rows=lambda: [])  # type: ignore[attr-defined]
    panel._matched_model = MagicMock()  # type: ignore[attr-defined]
    panel._unmatched_model = MagicMock()  # type: ignore[attr-defined]
    panel._view_bar = SimpleNamespace(current_view=lambda: VIEW_CONTENT)  # type: ignore[attr-defined]
    panel._content_view = SimpleNamespace(poster_cards=lambda: [])  # type: ignore[attr-defined]
    panel._clear_all_poster_grids = MagicMock()  # type: ignore[attr-defined]
    panel._apply_list_content_for_view_key = MagicMock()  # type: ignore[attr-defined]
    panel._ensure_poster_grid_for_view_key = MagicMock(return_value=[])  # type: ignore[attr-defined]
    panel._refresh_all_poster_pixmaps = MagicMock()  # type: ignore[attr-defined]
    panel._selectable_index = MagicMock(return_value=0)  # type: ignore[attr-defined]
    panel._on_selection = MagicMock()  # type: ignore[attr-defined]

    panel._sync_views_from_model()  # type: ignore[attr-defined]

    panel._on_selection.assert_called_once_with(-1)  # type: ignore[attr-defined]


def test_unified_index_selectable_index_and_state_helpers(monkeypatch) -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    group_a = _group("a.mkv")
    group_b = _group("b.mkv")
    panel._rows = [group_a, group_b]  # type: ignore[attr-defined]
    assert panel._unified_index_for_group(group_a) == 0  # type: ignore[attr-defined]
    assert panel._unified_index_for_group(SimpleNamespace(members=())) == -1  # type: ignore[attr-defined]
    assert panel._unified_index_for_group(_group("missing.mkv")) == -1  # type: ignore[attr-defined]

    panel._pending_selected_index = 1  # type: ignore[attr-defined]
    panel._selected_index = 0  # type: ignore[attr-defined]
    assert panel._selectable_index(3) == 1  # type: ignore[attr-defined]
    assert panel._pending_selected_index == -1  # type: ignore[attr-defined]
    assert panel._selectable_index(3) == 0  # type: ignore[attr-defined]
    panel._selected_index = 9  # type: ignore[attr-defined]
    assert panel._selectable_index(3) == 0  # type: ignore[attr-defined]
    assert panel._selectable_index(0) == -1  # type: ignore[attr-defined]

    saved: list[dict[str, object]] = []
    monkeypatch.setattr(panel_state_module, "save_all", lambda payload: saved.append(payload))
    panel._restoring_state = True  # type: ignore[attr-defined]
    panel._view_bar = SimpleNamespace(current_view=lambda: VIEW_ICON_M)  # type: ignore[attr-defined]
    panel._persist_ui_state()  # type: ignore[attr-defined]
    assert saved == []


def test_restore_ui_state_and_poster_image_loaded_handle_edge_cases(monkeypatch) -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    monkeypatch.setattr(panel_state_module, "load_all", lambda: {"ui_state": []})
    view_calls: list[str] = []
    panel._on_view_changed = lambda key: view_calls.append(key)  # type: ignore[attr-defined]

    panel._restore_ui_state()  # type: ignore[attr-defined]

    assert view_calls
    assert panel._pending_selected_index == -1  # type: ignore[attr-defined]

    pix_card = SimpleNamespace(set_pixmap=MagicMock())
    null_card = SimpleNamespace(set_pixmap=MagicMock())
    panel._cards_by_url = {"poster": [pix_card, null_card]}  # type: ignore[attr-defined]
    panel._on_poster_image_loaded("poster", SimpleNamespace(isNull=lambda: False))  # type: ignore[attr-defined]
    panel._on_poster_image_loaded("poster", SimpleNamespace(isNull=lambda: True))  # type: ignore[attr-defined]
    pix_card.set_pixmap.assert_any_call(None)
    null_card.set_pixmap.assert_any_call(None)


def test_icon_grid_click_keeps_details_visible_and_selects() -> None:
    panel = PipelineResultPanel.__new__(PipelineResultPanel)
    panel._set_details_pane_visible = MagicMock()  # type: ignore[attr-defined]
    panel._on_selection = MagicMock()  # type: ignore[attr-defined]

    panel._on_icon_grid_card_clicked(2)  # type: ignore[attr-defined]
    panel._on_icon_grid_card_clicked(1)  # type: ignore[attr-defined]

    assert panel._set_details_pane_visible.call_count == 2  # type: ignore[attr-defined]
    assert panel._on_selection.call_args_list[0].args == (2,)  # type: ignore[attr-defined]
    assert panel._on_selection.call_args_list[1].args == (1,)  # type: ignore[attr-defined]
