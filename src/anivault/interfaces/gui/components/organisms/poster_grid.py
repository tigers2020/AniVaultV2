"""poster_grid.py

가로 폭에 따라 열 수가 바뀌는 QScrollArea+QGridLayout 포스터 카드 그리드.

Author: Pom Kim
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from anivault.constants.gui.theme import (
    POSTER_GRID_MARGINS,
    POSTER_GRID_MIN_CARD_WIDTH,
    POSTER_GRID_SPACING,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, PosterCard
from anivault.interfaces.gui.components.molecules.poster_card import (
    CARD_LAYOUT_SPACING_COMPACT_PX,
    CARD_LAYOUT_SPACING_POSTER_PX,
    NON_COMPACT_BODY_HEIGHT_PX,
    POSTER_IMAGE_ASPECT_HW,
)
from anivault.interfaces.gui.themes import get_current_density_key, on_density_changed


def _column_count(width: int, *, min_card: int, grid_spacing: int) -> int:
    """주어진 뷰포트 너비에서 들어갈 그리드 열 개수를 계산한다.

    Args:
        width: 컨테이너 너비(픽셀).
        min_card: 카드 최소 너비.
        grid_spacing: 셀 간격.

    Returns:
        1 이상의 열 개수.
    """
    return max(1, (width + grid_spacing) // (min_card + grid_spacing))


class _GridContainer(QWidget):
    """너비·밀도 변경 시 그리드를 다시 배치하는 내부 컨테이너."""

    def __init__(
        self,
        min_card_width: int | None = POSTER_GRID_MIN_CARD_WIDTH,
        parent=None,
        *,
        body_below_image_px: int | None = None,
    ):
        """그리드 레이아웃·밀도 변경 콜백을 초기화한다.

        Args:
            self: 이 컨테이너.
            min_card_width: 카드 최소 너비. None이면 테마 기본값 사용.
            parent: Qt 부모.
            body_below_image_px: 이미지 아래 텍스트 영역 높이(컴팩트 카드용).
                None이면 포스터 카드 기본(큰 본문 + 포스터 간격)을 쓴다.

        Returns:
            None.
        """
        super().__init__(parent)
        self._min_card_width = min_card_width
        self._body_below_image_px = body_below_image_px
        self._grid_spacing = POSTER_GRID_SPACING
        # Outer column: grid (intrinsic height) + stretch below. Without this,
        # QGridLayout distributes extra viewport height *between* rows, making
        # row gaps much larger than horizontal GRID_SPACING when maximized.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*POSTER_GRID_MARGINS)
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
        """카드 목록을 저장하고 그리드를 처음부터 다시 배치한다.

        Args:
            self: 이 컨테이너.
            cards: PosterCard 목록.

        Returns:
            None.
        """
        self._cards = list(cards)
        self._last_cols = 0
        self._last_width = 0
        self._relayout()

    def _relayout(self) -> None:
        """현재 폭·간격·카드 수에 맞춰 그리드 셀을 채우고 최소 높이를 갱신한다.

        Args:
            self: 이 컨테이너.

        Returns:
            None.
        """
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item is None:
                break
            # Keep widgets parented to this container. setParent(None) would briefly
            # promote each card to a top-level window during large-grid relayout.
        if not self._cards:
            return

        grid_spacing = theme.poster_grid_spacing_px()
        self._grid.setSpacing(grid_spacing)

        mc = (
            self._min_card_width
            if self._min_card_width is not None
            else theme.poster_min_card_width_px()
        )
        width_px = self.width()
        if width_px <= 0:
            width_px = mc * 2 + grid_spacing
        cols = _column_count(width_px, min_card=mc, grid_spacing=grid_spacing)
        self._last_cols = cols
        self._last_width = width_px
        # One size for all cards so height never "shrinks" by column
        card_w = max(mc, (width_px - (cols - 1) * grid_spacing) // cols)
        if self._body_below_image_px is None:
            below_img = CARD_LAYOUT_SPACING_POSTER_PX + NON_COMPACT_BODY_HEIGHT_PX
        else:
            below_img = CARD_LAYOUT_SPACING_COMPACT_PX + self._body_below_image_px
        card_h = int(card_w * POSTER_IMAGE_ASPECT_HW) + below_img
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
        layout = self.layout()
        outer_m = layout.contentsMargins() if layout is not None else None
        extra_h = grid_m.top() + grid_m.bottom()
        if outer_m is not None:
            extra_h += outer_m.top() + outer_m.bottom()
        self.setMinimumHeight(rows * card_h + (rows - 1) * grid_spacing + extra_h)
        self._last_density_key = get_current_density_key()

    def resizeEvent(self, event) -> None:
        """너비 또는 UI 밀도 키가 바뀌면 그리드를 재배치한다.

        Args:
            self: 이 컨테이너.
            event: Qt 리사이즈 이벤트.

        Returns:
            None.
        """
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
        """밀도 테마 변경 시 카드가 있으면 레이아웃을 다시 계산한다.

        Args:
            self: 이 컨테이너.

        Returns:
            None.
        """
        if self._cards:
            self._relayout()


class PosterGrid(QFrame):
    """세로형 비율 포스터 카드 그리드. 사용 가능한 너비로 열 수 결정."""

    def __init__(
        self,
        min_card_width: int | None = None,
        show_header: bool = True,
        parent=None,
        *,
        body_below_image_px: int | None = None,
    ):
        """스크롤 영역·내부 그리드 컨테이너·선택적 헤더를 구성한다.

        Args:
            self: 이 그리드 위젯.
            min_card_width: 카드 최소 너비. None이면 기본값.
            show_header: 상단 PanelHeader 표시 여부.
            parent: Qt 부모.
            body_below_image_px: 이미지 아래 텍스트 영역 높이(컴팩트 카드와 맞출 때).
                None이면 포스터 카드 기본 본문 높이를 쓴다.

        Returns:
            None.
        """
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
        self._container = _GridContainer(
            min_card_width=min_card_width,
            body_below_image_px=body_below_image_px,
        )
        scroll.setWidget(self._container)
        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())

    def set_cards(self, cards: list[PosterCard]) -> None:
        """기존 카드를 정리한 뒤 새 카드 목록으로 그리드를 채운다.

        Args:
            self: 이 그리드 위젯.
            cards: 표시할 PosterCard 목록.

        Returns:
            None.
        """
        for c in self._container._cards:
            c.deleteLater()
        self._container.set_cards(cards)

    def cards(self) -> list[PosterCard]:
        """현재 그리드에 올라간 포스터 카드 목록의 복사본을 반환한다.

        Args:
            self: 이 그리드 위젯.

        Returns:
            PosterCard 리스트 복사본.
        """
        return list(self._container._cards)
