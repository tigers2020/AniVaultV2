"""Pipeline result panel: integrated table + poster grid with view toggle."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QStackedWidget,
    QSplitter,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import (
    PanelHeader,
    ViewToggleBar,
    PosterCard,
)
from anivault.interfaces.gui.components.organisms.compact_list_view import CompactListView
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import DetailsPane
from anivault.interfaces.gui.components.organisms.pipeline_table import PipelineTable
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid
from anivault.interfaces.gui.components.organisms.preview_pane import PreviewPane
from anivault.interfaces.gui.components.organisms.tile_view import TileView
from anivault.interfaces.gui.models import PipelineRow

from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_DETAILS,
    VIEW_LIST,
    VIEW_TILES,
    VIEW_CONTENT,
    VIEW_ICON_XL,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
)

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

ICON_SIZES = {VIEW_ICON_XL: 220, VIEW_ICON_L: 180, VIEW_ICON_M: 140, VIEW_ICON_S: 100}


class PipelineResultPanel(QFrame):
    """Unified pipeline result with view toggle and optional side panes."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[PipelineRow] = []
        self._selected_index = -1
        self._pane_mode: str | None = None  # "details" | "preview" | None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        view_bar = ViewToggleBar()
        header = PanelHeader(
            "Pipeline Result",
            "테이블 또는 포스터 그리드로 결과 보기. 보기 메뉴에서 레이아웃을 선택하세요.",
            right_widget=view_bar,
        )
        layout.addWidget(header)

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Main content: stacked views
        self._stack = QStackedWidget()

        # 0: Details (table)
        table = PipelineTable(show_header=False)
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
        self._pane_stack.addWidget(QWidget())  # empty
        self._details_pane = DetailsPane()
        self._preview_pane = PreviewPane()
        self._pane_stack.addWidget(self._details_pane)
        self._pane_stack.addWidget(self._preview_pane)
        main_splitter.addWidget(self._pane_stack)
        self._main_splitter = main_splitter
        self._pane_width = 260
        main_splitter.setSizes([800, 0])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)

        layout.addWidget(main_splitter)
        self.setStyleSheet(theme.card_panel())

        view_bar.view_changed.connect(self._on_view_changed)
        view_bar.details_pane_changed.connect(self._on_details_pane)
        view_bar.preview_pane_changed.connect(self._on_preview_pane)

    def _on_view_changed(self, key: str) -> None:
        if key in VIEW_TO_INDEX:
            self._stack.setCurrentIndex(VIEW_TO_INDEX[key])
        view_bar = self.findChild(ViewToggleBar)
        if view_bar:
            view_bar.set_current_view(key)

    def _on_selection(self, index: int) -> None:
        self._selected_index = index
        self.selection_changed.emit(index)
        row = self._rows[index] if 0 <= index < len(self._rows) else None
        self._details_pane.set_row(row)
        self._preview_pane.set_row(row)

    def _on_details_pane(self, checked: bool) -> None:
        if checked:
            self._pane_mode = "details"
            vtb = self.findChild(ViewToggleBar)
            if vtb:
                vtb.set_preview_pane_checked(False)
            self._pane_stack.setCurrentIndex(1)
            w = self._main_splitter.width()
            self._main_splitter.setSizes([max(200, w - self._pane_width), self._pane_width])
        else:
            if self._pane_mode == "details":
                self._pane_mode = None
            self._pane_stack.setCurrentIndex(0)
            w = self._main_splitter.width()
            self._main_splitter.setSizes([w, 0])

    def _on_preview_pane(self, checked: bool) -> None:
        if checked:
            self._pane_mode = "preview"
            vtb = self.findChild(ViewToggleBar)
            if vtb:
                vtb.set_details_pane_checked(False)
            self._pane_stack.setCurrentIndex(2)
            w = self._main_splitter.width()
            self._main_splitter.setSizes([max(200, w - self._pane_width), self._pane_width])
        else:
            if self._pane_mode == "preview":
                self._pane_mode = None
            self._pane_stack.setCurrentIndex(0)
            w = self._main_splitter.width()
            self._main_splitter.setSizes([w, 0])

    def _make_card_clickable(self, card: PosterCard, index: int) -> None:
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda e, idx=index: self._on_selection(idx)

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._rows = list(rows)
        cards = [
            PosterCard(
                title=r.tmdb_korean_title_group,
                meta=f"Parsed: {r.parsed_title}\nYear: {r.year} • {r.season} • {r.resolution}",
                path=r.target_path,
                image_url=r.poster_url,
            )
            for r in rows
        ]
        for i, card in enumerate(cards):
            self._make_card_clickable(card, i)

        self._table.set_rows(rows)
        self._list_view.set_rows(rows)
        self._tile_view.set_cards(cards)
        self._content_view.set_rows(rows)
        for grid in self._poster_grids.values():
            grid.set_cards(cards)

        if rows and self._selected_index < 0:
            self._on_selection(0)
