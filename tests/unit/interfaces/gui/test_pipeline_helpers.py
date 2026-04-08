from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.interfaces.gui.components.molecules.view_toggle_bar import VIEW_CONTENT, VIEW_DETAILS
from anivault.interfaces.gui.models import PipelineRow, group_pipeline_rows
from anivault.interfaces.gui.templates import pipeline_result_ui_state as ui_state_module
from anivault.interfaces.gui.templates.pipeline_result_ui_state import (
    load_normalized_pipeline_ui_state_from_settings,
    normalize_pipeline_ui_state,
    restore_pipeline_result_panel_ui_state,
    save_pipeline_result_panel_ui_state,
)
from anivault.interfaces.gui.templates.pipeline_selection_sync import (
    on_split_table_selection,
    sync_split_tables_selection,
    unified_index_for_group,
)
from anivault.interfaces.gui.templates.poster_view_binder import PosterViewBinder


def _group(path: str, *, poster_url: str = "", matched: bool = True):
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
        poster_url=poster_url,
        backdrop_url="",
        target_path="F:/Library/show.mkv" if matched else "",
    )
    return group_pipeline_rows([row])[0]


class _FakeSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class _FakePixmap:
    def __init__(self, *, is_null: bool = False) -> None:
        self._is_null = is_null

    def isNull(self) -> bool:
        return self._is_null


class _FakeCard:
    def __init__(self, image_url: str) -> None:
        self.image_url = image_url
        self.pixmaps: list[object | None] = []

    def set_pixmap(self, pixmap) -> None:
        self.pixmaps.append(pixmap)


def test_pipeline_result_ui_state_helpers_round_trip(monkeypatch) -> None:
    normalized = normalize_pipeline_ui_state(
        {
            "view_key": "tiles",
            "details_pane": True,
            "preview_pane": True,
            "selected_index": 2,
        }
    )
    calls: list[tuple[str, object]] = []
    restore_pipeline_result_panel_ui_state(
        normalized,
        set_restoring=lambda value: calls.append(("restoring", value)),
        set_pending_selected_index=lambda value: calls.append(("selected", value)),
        apply_view_key=lambda value: calls.append(("view", value)),
        apply_details_pane=lambda value: calls.append(("details", value)),
        apply_preview_pane=lambda value: calls.append(("preview", value)),
    )
    monkeypatch.setattr(
        ui_state_module,
        "load_all",
        lambda: {"ui_state": {"pipeline_results": {"view_key": "list", "selected_index": 5}}},
    )
    assert normalized["view_key"] == VIEW_CONTENT
    assert calls[0] == ("restoring", True)
    assert calls[-1] == ("restoring", False)
    assert load_normalized_pipeline_ui_state_from_settings()["view_key"] == VIEW_DETAILS

    payloads: list[dict[str, object]] = []
    monkeypatch.setattr(ui_state_module, "save_all", lambda data: payloads.append(data))
    monkeypatch.setattr(ui_state_module, "load_all", lambda: {"ui_state": "bad"})
    save_pipeline_result_panel_ui_state(normalized)
    assert payloads[0]["ui_state"]["pipeline_results"]["selected_index"] == 2  # type: ignore[index]


def test_pipeline_selection_sync_helpers_cover_all_paths() -> None:
    matched = _group("F:/Anime/show01.mkv")
    unmatched = _group("F:/Anime/show02.mkv", matched=False)
    unified_rows = [matched, unmatched]
    assert unified_index_for_group(unified_rows, matched) == 0
    assert unified_index_for_group(unified_rows, SimpleNamespace(members=[])) == -1

    matched_model = SimpleNamespace(rows=lambda: [matched])
    unmatched_model = SimpleNamespace(rows=lambda: [unmatched])
    matched_table = MagicMock()
    unmatched_table = MagicMock()
    sync_split_tables_selection(
        unified_rows,
        1,
        matched_model,
        unmatched_model,
        matched_table,
        unmatched_table,
    )
    sync_split_tables_selection(
        unified_rows,
        -1,
        matched_model,
        unmatched_model,
        matched_table,
        unmatched_table,
    )
    applied: list[int] = []
    on_split_table_selection(
        "matched",
        0,
        unified_rows,
        matched_model,
        unmatched_model,
        lambda index: applied.append(index),
    )
    on_split_table_selection(
        "matched",
        99,
        unified_rows,
        matched_model,
        unmatched_model,
        lambda index: applied.append(index),
    )
    assert applied == [0]


def test_poster_view_binder_updates_cards_and_preview(monkeypatch) -> None:
    preview = MagicMock()
    image_loader = SimpleNamespace(
        loaded=_FakeSignal(),
        get=lambda url: _FakePixmap() if url == "cached" else None,
        load=MagicMock(),
    )
    binder = PosterViewBinder(image_loader, preview)
    cards = [_FakeCard("cached"), _FakeCard("remote"), _FakeCard("")]

    binder.refresh_poster_pixmaps(cards)
    binder.schedule_preview_image(_group("F:/Anime/show01.mkv", poster_url="cached"))
    binder.schedule_preview_image(_group("F:/Anime/show02.mkv", poster_url="remote"))
    image_loader.loaded.callback("remote", _FakePixmap())
    binder.schedule_preview_image(None)
    image_loader.loaded.callback("remote", _FakePixmap(is_null=True))

    assert cards[0].pixmaps and isinstance(cards[0].pixmaps[0], _FakePixmap)
    image_loader.load.assert_called_with("remote")
    assert preview.set_pixmap.call_count >= 2
