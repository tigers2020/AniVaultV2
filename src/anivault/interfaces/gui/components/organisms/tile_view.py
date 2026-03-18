"""Tile view: large cards with image + title + parsed/tmdb/path summary."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PosterCard

TILE_MIN_WIDTH = 200


def _make_clickable_card(card: PosterCard, index: int, callback) -> None:
    """Replace mousePressEvent to emit selection."""

    def _on_click(event):
        callback(index)

    card.mousePressEvent = _on_click  # type: ignore[method-assign]
    card.setCursor(Qt.CursorShape.PointingHandCursor)


GRID_SPACING = 20
POSTER_ASPECT = 3 / 2


def _tile_column_count(width: int) -> int:
    return max(1, (width + GRID_SPACING) // (TILE_MIN_WIDTH + GRID_SPACING))


class _TileContainer(QWidget):
    """Grid of tile cards. 2-3 columns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setSpacing(GRID_SPACING)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._cards: list[PosterCard] = []
        self._last_width = 0

    def set_cards(self, cards: list[PosterCard]) -> None:
        self._cards = list(cards)
        self._last_width = 0
        self._relayout()

    def _relayout(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if not self._cards:
            return
        w = self.width()
        if w <= 0:
            w = TILE_MIN_WIDTH * 2 + GRID_SPACING
        cols = _tile_column_count(w)
        card_w = max(TILE_MIN_WIDTH, (w - (cols - 1) * GRID_SPACING) // cols)
        card_h = int(card_w * POSTER_ASPECT)
        align = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        for i, card in enumerate(self._cards):
            card.setFixedSize(card_w, card_h)
            card.setParent(self)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col, align)
        rows = (len(self._cards) + cols - 1) // cols
        self.setMinimumHeight(rows * card_h + (rows - 1) * GRID_SPACING)
        self._last_width = w

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.width() != self._last_width and self._cards:
            self._relayout()


class TileView(QFrame):
    """Tile layout: larger cards than poster grid."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        self._container = _TileContainer()
        scroll.setWidget(self._container)
        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())

    def set_cards(self, cards: list[PosterCard]) -> None:
        for c in self._container._cards:
            c.deleteLater()
        for i, card in enumerate(cards):
            _make_clickable_card(card, i, self._on_select)
        self._container.set_cards(cards)

    def _on_select(self, index: int) -> None:
        self.selection_changed.emit(index)
