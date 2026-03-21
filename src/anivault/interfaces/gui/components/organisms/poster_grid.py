"""Poster grid: QScrollArea + QGridLayout + PosterCards. Dynamic columns by width."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, PosterCard
from anivault.interfaces.gui.components.molecules.poster_card import (
    CARD_LAYOUT_SPACING_POSTER_PX,
    NON_COMPACT_BODY_HEIGHT_PX,
    POSTER_IMAGE_ASPECT_HW,
)
from anivault.interfaces.gui.themes import get_current_density_key, on_density_changed

MIN_CARD_WIDTH = 140
GRID_SPACING = 12
GRID_MARGINS = (0, 0, 0, 0)


def _column_count(width: int, *, min_card: int, grid_spacing: int) -> int:
    return max(1, (width + grid_spacing) // (min_card + grid_spacing))


class _GridContainer(QWidget):
    """Container that relayouts grid when width changes."""

    def __init__(self, min_card_width: int | None = MIN_CARD_WIDTH, parent=None):
        super().__init__(parent)
        self._min_card_width = min_card_width
        # Outer column: grid (intrinsic height) + stretch below. Without this,
        # QGridLayout distributes extra viewport height *between* rows, making
        # row gaps much larger than horizontal GRID_SPACING when maximized.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*GRID_MARGINS)
        outer.setSpacing(0)
        self._grid = QGridLayout()
        self._grid.setSpacing(theme.poster_grid_spacing_px())
        self._grid.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(self._grid)
        outer.addStretch(1)
        self._cards: list[PosterCard] = []
        self._last_cols = 0
        self._last_width = 0
        self._last_density_key = get_current_density_key()
        on_density_changed(self._apply_responsive_metrics)

    def set_cards(self, cards: list[PosterCard]) -> None:
        self._cards = list(cards)
        self._last_cols = 0
        self._last_width = 0
        self._relayout()

    def _relayout(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if not self._cards:
            return

        grid_spacing = theme.poster_grid_spacing_px()
        self._grid.setSpacing(grid_spacing)

        mc = (
            self._min_card_width
            if self._min_card_width is not None
            else theme.poster_min_card_width_px()
        )
        w = self.width()
        if w <= 0:
            w = mc * 2 + grid_spacing
        cols = _column_count(w, min_card=mc, grid_spacing=grid_spacing)
        self._last_cols = cols
        self._last_width = w
        # One size for all cards so height never "shrinks" by column
        card_w = max(mc, (w - (cols - 1) * grid_spacing) // cols)
        card_h = (
            int(card_w * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX
        )
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
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
        self._last_density_key = get_current_density_key()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = self.width()
        if w <= 0:
            return

        density_key = get_current_density_key()
        if w != self._last_width or density_key != self._last_density_key:
            self._last_width = w
            self._last_density_key = density_key
            self._relayout()

    def _apply_responsive_metrics(self) -> None:
        if self._cards:
            self._relayout()


class PosterGrid(QFrame):
    """Grid of poster cards. Portrait 2:3 ratio; columns from available width."""

    def __init__(
        self,
        min_card_width: int | None = None,
        show_header: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if show_header:
            layout.addWidget(
                PanelHeader(
                    "Final Move Preview",
                    "TMDB poster 이미지를 기준으로 최종 이동 결과를 카드 그리드로 미리보기",
                    pill_text="Poster Grid",
                    pill_color="green",
                )
            )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Ensure the scroll viewport consumes all available height, so cards
        # don't appear vertically "centered" when the window is maximized.
        scroll.setViewportMargins(0, 0, 0, 0)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        scroll.setHorizontalScrollBarPolicy(scroll.horizontalScrollBarPolicy())
        scroll.setStyleSheet(theme.scroll_area_transparent())
        self._container = _GridContainer(min_card_width=min_card_width)
        scroll.setWidget(self._container)
        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())

    def set_cards(self, cards: list[PosterCard]) -> None:
        for c in self._container._cards:
            c.deleteLater()
        self._container.set_cards(cards)
