"""Pipeline result template: integrates organisms with view toggle."""

from __future__ import annotations

from typing import Literal, TypedDict

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui.components.molecules import (
    PanelHeader,
    PosterCard,
    ViewToggleBar,
)
from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_CONTENT,
    VIEW_DETAILS,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_ICON_XL,
    VIEW_LIST,
    VIEW_TILES,
)
from anivault.interfaces.gui.components.organisms.compact_list_view import CompactListView
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import DetailsPane
from anivault.interfaces.gui.components.organisms.pipeline_table import PipelineTable
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid
from anivault.interfaces.gui.components.organisms.preview_pane import PreviewPane
from anivault.interfaces.gui.components.organisms.tile_view import TileView
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineTableModel
from anivault.interfaces.gui.services.image_loader import ImageLoader
from anivault.interfaces.gui.settings_storage import load_all, save_all

VIEW_TO_INDEX = {
    VIEW_DETAILS: 0,
    VIEW_LIST: 1,
    VIEW_TILES: 2,
    VIEW_CONTENT: 3,
    VIEW_ICON_XL: 4,
    VIEW_ICON_L: 5,
    VIEW_ICON_M: 6,
    VIEW_ICON_S: 7,
}


class PipelineResultUiState(TypedDict):
    """Persisted UI state payload for PipelineResultPanel."""

    view_key: str
    details_pane: bool
    preview_pane: bool
    selected_index: int


ICON_SIZES = {VIEW_ICON_XL: 220, VIEW_ICON_L: 180, VIEW_ICON_M: 140, VIEW_ICON_S: 100}
DEFAULT_UI_STATE: PipelineResultUiState = {
    "view_key": VIEW_DETAILS,
    "details_pane": False,
    "preview_pane": False,
    "selected_index": -1,
}


class PipelineResultPanel(QFrame):
    """Unified pipeline result with view toggle and optional side panes."""

    selection_changed = Signal(int)

    def __init__(
        self,
        model: PipelineTableModel | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._model = model if model is not None else PipelineTableModel()
        self._rows: list[PipelineGroupRow] = []
        self._selected_index = -1
        self._pane_mode: str | None = None  # "details" | "preview" | None
        self._restoring_state = False
        self._pending_selected_index = -1
        self._cards_by_url: dict[str, list[PosterCard]] = {}
        self._image_loader = ImageLoader(self)
        self._image_loader.loaded.connect(self._on_poster_image_loaded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view_bar = ViewToggleBar()
        self._header = PanelHeader(
            "Pipeline Result",
            "테이블 또는 포스터 그리드로 결과 보기. 보기 메뉴에서 레이아웃을 선택하세요.",
            right_widget=self._view_bar,
        )
        layout.addWidget(self._header)
        # Keep the header ("label") height stable; let the table/content consume remaining space.
        self._header.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        )
        self._sync_header_height()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Main content: stacked views
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self._stack.setMinimumHeight(0)

        # 0: Details (table) — use shared model when provided
        table = PipelineTable(show_header=False, model=self._model)
        table.selection_changed.connect(self._on_selection)
        self._stack.addWidget(table)
        self._table = table

        # 1: List
        list_view = CompactListView()
        list_view.selection_changed.connect(self._on_selection)
        self._stack.addWidget(list_view)
        self._list_view = list_view

        # 2: Tiles
        tile_view = TileView()
        tile_view.selection_changed.connect(self._on_selection)
        self._stack.addWidget(tile_view)
        self._tile_view = tile_view

        # 3: Content
        content_view = ContentView()
        content_view.selection_changed.connect(self._on_selection)
        self._stack.addWidget(content_view)
        self._content_view = content_view

        # 4-7: Icon grids (XL, L, M, S)
        self._poster_grids: dict[str, PosterGrid] = {}
        for key in (VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S):
            grid = PosterGrid(min_card_width=ICON_SIZES[key], show_header=False)
            self._stack.addWidget(grid)
            self._poster_grids[key] = grid

        main_splitter.addWidget(self._stack)

        # Right pane placeholder (DetailsPane or PreviewPane)
        self._pane_stack = QStackedWidget()
        self._pane_stack.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        )
        self._pane_stack.setMinimumHeight(0)
        self._pane_stack.addWidget(QWidget())  # empty
        self._details_pane = DetailsPane()
        self._preview_pane = PreviewPane()
        self._pane_stack.addWidget(self._details_pane)
        self._pane_stack.addWidget(self._preview_pane)
        main_splitter.addWidget(self._pane_stack)
        self._main_splitter = main_splitter
        self._main_splitter.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self._main_splitter.setMinimumHeight(0)
        self._pane_width = 340
        self._main_min_width = 320
        main_splitter.setSizes([960, 0])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)

        layout.addWidget(main_splitter)
        # Vertical stretch: header(0) is fixed, splitter(1) fills remaining space.
        layout.setStretchFactor(self._header, 0)
        layout.setStretchFactor(main_splitter, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.setMinimumHeight(0)

        self._view_bar.view_changed.connect(self._on_view_changed)
        self._view_bar.details_pane_changed.connect(self._on_details_pane)
        self._view_bar.preview_pane_changed.connect(self._on_preview_pane)

        # Sync list/tile/content/poster when model changes
        self._model.modelReset.connect(self._sync_views_from_model)
        self._restore_ui_state()

    def _on_view_changed(self, key: str) -> None:
        if key in VIEW_TO_INDEX:
            self._stack.setCurrentIndex(VIEW_TO_INDEX[key])
        self._view_bar.set_current_view(key)
        self._persist_ui_state()

    def _on_selection(self, index: int) -> None:
        self._selected_index = index
        self.selection_changed.emit(index)
        row = self._rows[index] if 0 <= index < len(self._rows) else None
        self._details_pane.set_row(row)
        self._preview_pane.set_row(row)
        self._persist_ui_state()

    def _on_details_pane(self, checked: bool) -> None:
        if checked:
            self._pane_mode = "details"
            self._pane_stack.setCurrentIndex(1)
            w = self._main_splitter.width()
            self._main_splitter.setSizes(
                [max(self._main_min_width, w - self._pane_width), self._pane_width]
            )
        else:
            # If both toggles are on, turning off the inactive one should not hide the
            # currently displayed pane.
            if self._pane_mode == "details":
                if self._view_bar.preview_pane_checked():
                    self._pane_mode = "preview"
                    self._pane_stack.setCurrentIndex(2)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes(
                        [max(self._main_min_width, w - self._pane_width), self._pane_width]
                    )
                else:
                    self._pane_mode = None
                    self._pane_stack.setCurrentIndex(0)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes([w, 0])
        self._persist_ui_state()

    def _on_preview_pane(self, checked: bool) -> None:
        if checked:
            self._pane_mode = "preview"
            self._pane_stack.setCurrentIndex(2)
            w = self._main_splitter.width()
            self._main_splitter.setSizes(
                [max(self._main_min_width, w - self._pane_width), self._pane_width]
            )
        else:
            if self._pane_mode == "preview":
                if self._view_bar.details_pane_checked():
                    self._pane_mode = "details"
                    self._pane_stack.setCurrentIndex(1)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes(
                        [max(self._main_min_width, w - self._pane_width), self._pane_width]
                    )
                else:
                    self._pane_mode = None
                    self._pane_stack.setCurrentIndex(0)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes([w, 0])
        self._persist_ui_state()

    def _make_card_clickable(self, card: PosterCard, index: int) -> None:
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda e, idx=index: self._on_selection(idx)  # type: ignore[method-assign,misc]

    def _on_poster_image_loaded(self, url: str, pixmap: QPixmap) -> None:
        for card in self._cards_by_url.get(url, []):
            card.set_pixmap(pixmap if not pixmap.isNull() else None)

    def _refresh_all_poster_pixmaps(self, cards: list[PosterCard]) -> None:
        self._cards_by_url.clear()
        for card in cards:
            u = (card.image_url or "").strip()
            if u.startswith("http"):
                self._cards_by_url.setdefault(u, []).append(card)
        for url in self._cards_by_url:
            cached = self._image_loader.get(url)
            if cached is not None:
                for c in self._cards_by_url[url]:
                    c.set_pixmap(cached)
            else:
                self._image_loader.load(url)

    def _sync_views_from_model(self) -> None:
        """Update list/tile/content/poster from model (called on modelReset)."""
        rows = self._model.rows()
        self._rows = list(rows)

        def _make_cards(variant: Literal["poster", "compact"]) -> list[PosterCard]:
            cards: list[PosterCard] = []
            for g in rows:
                title = (g.tmdb_korean_title_group or "").strip() or (g.parsed_title or "").strip()
                meta_lines = [
                    f"Parsed: {g.parsed_title}",
                    f"Year: {g.year} • {g.season} • {g.resolution}",
                ]
                if len(g.members) > 1:
                    meta_lines.insert(0, f"{len(g.members)} files")
                cards.append(
                    PosterCard(
                        title=title,
                        meta="\n".join(meta_lines),
                        path=g.target_path,
                        image_url=g.poster_url,
                        variant=variant,
                    )
                )
            return cards

        tiles_cards = _make_cards("poster")
        for i, card in enumerate(tiles_cards):
            self._make_card_clickable(card, i)
        self._list_view.set_rows(rows)
        self._tile_view.set_cards(tiles_cards)
        self._content_view.set_rows(rows)
        all_poster_cards: list[PosterCard] = []
        all_poster_cards.extend(tiles_cards)
        all_poster_cards.extend(self._content_view.poster_cards())
        for grid in self._poster_grids.values():
            grid_cards = _make_cards("compact")
            for i, card in enumerate(grid_cards):
                self._make_card_clickable(card, i)
            grid.set_cards(grid_cards)
            all_poster_cards.extend(grid_cards)
        self._refresh_all_poster_pixmaps(all_poster_cards)
        if rows:
            index = self._selectable_index(len(rows))
            self._on_selection(index)
        else:
            self._on_selection(-1)

    def _selectable_index(self, length: int) -> int:
        """Return valid selection index for current/pending state."""
        if length <= 0:
            return -1
        if 0 <= self._pending_selected_index < length:
            idx = self._pending_selected_index
            self._pending_selected_index = -1
            return idx
        if 0 <= self._selected_index < length:
            return self._selected_index
        return 0

    def _restore_ui_state(self) -> None:
        """Apply persisted Pipeline Result UI state from settings storage."""
        ui_state = load_all().get("ui_state", {})
        pipeline_state = {}
        if isinstance(ui_state, dict):
            raw = ui_state.get("pipeline_results", {})
            if isinstance(raw, dict):
                pipeline_state = raw
        normalized = self._normalize_ui_state(pipeline_state)
        self._restoring_state = True
        self._pending_selected_index = normalized["selected_index"]
        self._on_view_changed(normalized["view_key"])
        self._on_details_pane(bool(normalized["details_pane"]))
        self._on_preview_pane(bool(normalized["preview_pane"]))
        self._restoring_state = False

    def _normalize_ui_state(self, data: dict[str, object]) -> PipelineResultUiState:
        """Normalize persisted ui_state payload to safe defaults."""
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
        if isinstance(view_key, str) and view_key in VIEW_TO_INDEX:
            normalized["view_key"] = view_key
        if isinstance(details_pane, bool):
            normalized["details_pane"] = details_pane
        if isinstance(preview_pane, bool):
            normalized["preview_pane"] = preview_pane
        if isinstance(selected_index, int):
            normalized["selected_index"] = selected_index
        return normalized

    def _persist_ui_state(self) -> None:
        """Persist current Pipeline Result UI state."""
        if self._restoring_state:
            return
        save_all(
            {
                "ui_state": {
                    "pipeline_results": {
                        "view_key": self._view_bar.current_view(),
                        "details_pane": self._view_bar.details_pane_checked(),
                        "preview_pane": self._view_bar.preview_pane_checked(),
                        "selected_index": self._selected_index,
                    }
                }
            }
        )

    def model(self) -> PipelineTableModel:
        """Return shared model for presenter updates."""
        return self._model

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        """Set group rows. Updates model (triggers _sync_views_from_model for list/tile/content/poster)."""
        self._model.set_rows(rows)

    def _sync_header_height(self) -> None:
        """Recompute header fixed height after style/font updates."""
        header_h = int(self._header.sizeHint().height())
        if header_h > 0:
            self._header.setFixedHeight(header_h)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_header_height()
