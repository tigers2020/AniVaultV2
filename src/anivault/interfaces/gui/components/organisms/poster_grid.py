"""Poster grid: QScrollArea + QGridLayout + PosterCards. Dynamic columns by width."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QGridLayout

from anivault.interfaces.gui.components.molecules import PanelHeader, PosterCard
from anivault.interfaces.gui import theme

MIN_CARD_WIDTH = 140
GRID_SPACING = 16
GRID_MARGINS = (0, 0, 0, 0)
# Portrait 2:3
POSTER_ASPECT = 3 / 2


def _column_count(width: int, min_card: int) -> int:
    return max(1, (width + GRID_SPACING) // (min_card + GRID_SPACING))


class _GridContainer(QWidget):
    """Container that relayouts grid when width changes."""

    def __init__(self, min_card_width: int = MIN_CARD_WIDTH, parent=None):
        super().__init__(parent)
        self._min_card_width = min_card_width
        self._grid = QGridLayout(self)
        self._grid.setSpacing(GRID_SPACING)
        self._grid.setContentsMargins(*GRID_MARGINS)
        self._cards: list[PosterCard] = []
        self._last_cols = 0
        self._last_width = 0

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
        w = self.width()
        mc = self._min_card_width
        if w <= 0:
            w = mc * 2 + GRID_SPACING
        cols = _column_count(w, mc)
        self._last_cols = cols
        self._last_width = w
        # One size for all cards so height never "shrinks" by column
        card_w = max(mc, (w - (cols - 1) * GRID_SPACING) // cols)
        card_h = int(card_w * POSTER_ASPECT)
        for c in range(cols):
            self._grid.setColumnStretch(c, 1)
        align = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        for i, card in enumerate(self._cards):
            card.setFixedSize(card_w, card_h)
            card.setParent(self)
            row, col = divmod(i, cols)
            self._grid.addWidget(card, row, col, align)
        rows = (len(self._cards) + cols - 1) // cols
        self.setMinimumHeight(rows * card_h + (rows - 1) * GRID_SPACING)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = self.width()
        if w <= 0:
            return
        if w != self._last_width:
            self._last_width = w
            self._relayout()


class PosterGrid(QFrame):
    """Grid of poster cards. Portrait 2:3 ratio; columns from available width."""

    def __init__(
        self,
        min_card_width: int = MIN_CARD_WIDTH,
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
