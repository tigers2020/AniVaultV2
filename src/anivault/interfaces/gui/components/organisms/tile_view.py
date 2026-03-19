"""Tile view: large cards with image + title + parsed/tmdb/path summary."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.themes import get_current_density_key, on_density_changed

TILE_MIN_WIDTH = 200


def _make_clickable_card(card: PosterCard, index: int, callback) -> None:
    """Replace mousePressEvent to emit selection."""

    def _on_click(event):
        callback(index)

    card.mousePressEvent = _on_click  # type: ignore[method-assign]
    card.setCursor(Qt.CursorShape.PointingHandCursor)


GRID_SPACING = 14
POSTER_ASPECT = 3 / 2


def _tile_column_count(width: int, *, min_card_width: int, grid_spacing: int) -> int:
    return max(1, (width + grid_spacing) // (min_card_width + grid_spacing))


class _TileContainer(QWidget):
    """Grid of tile cards. 2-3 columns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Grid + bottom stretch so extra height stays below the last row, not
        # between rows (matches horizontal GRID_SPACING between card rows).
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self._grid = QGridLayout()
        self._grid.setSpacing(theme.tile_grid_spacing_px())
        self._grid.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self._grid)
        outer.addStretch(1)
        self._cards: list[PosterCard] = []
        self._last_width = 0
        self._last_density_key = get_current_density_key()
        on_density_changed(self._apply_responsive_metrics)

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

        min_card_width = theme.tile_min_width_px()
        grid_spacing = theme.tile_grid_spacing_px()
        self._grid.setSpacing(grid_spacing)

        w = self.width()
        if w <= 0:
            w = min_card_width * 2 + grid_spacing
        cols = _tile_column_count(w, min_card_width=min_card_width, grid_spacing=grid_spacing)
        card_w = max(min_card_width, (w - (cols - 1) * grid_spacing) // cols)
        card_h = int(card_w * POSTER_ASPECT)
        align = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        for i, card in enumerate(self._cards):
            card.setFixedSize(card_w, card_h)
            card.setParent(self)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col, align)
        rows = (len(self._cards) + cols - 1) // cols
        grid_m = self._grid.contentsMargins()
        outer_m = self.layout().contentsMargins() if self.layout() is not None else None
        extra_h = grid_m.top() + grid_m.bottom()
        if outer_m is not None:
            extra_h += outer_m.top() + outer_m.bottom()
        self.setMinimumHeight(rows * card_h + (rows - 1) * grid_spacing + extra_h)
        self._last_width = w
        self._last_density_key = get_current_density_key()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        density_key = get_current_density_key()
        if (
            self.width() != self._last_width or density_key != self._last_density_key
        ) and self._cards:
            self._relayout()

    def _apply_responsive_metrics(self) -> None:
        # density changes (height-only resize) do not necessarily trigger a
        # width-driven relayout, so we listen to theme-density change.
        if self._cards:
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
        # Ensure the scroll viewport consumes all available height, so cards
        # don't appear vertically "centered" when the window is maximized.
        scroll.setViewportMargins(0, 0, 0, 0)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
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
