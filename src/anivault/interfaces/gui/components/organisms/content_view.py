"""Content view: top = large preview of selected, bottom = metadata. List on left."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QSplitter,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.models import PipelineRow


class ContentView(QFrame):
    """Content layout: list on left, large preview + metadata on right."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: compact list
        left = QFrame()
        left.setMinimumWidth(200)
        left.setMaximumWidth(320)
        left.setStyleSheet(theme.card_panel())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet(theme.scroll_area_transparent())
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(4)
        left_scroll.setWidget(self._list_container)
        left_layout.addWidget(left_scroll)
        splitter.addWidget(left)

        # Right: preview + metadata
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumHeight(240)
        self._preview_label.setStyleSheet(theme.poster_card_image())
        self._preview_label.setText("항목을 선택하세요")
        self._preview_label.setScaledContents(False)
        right_layout.addWidget(self._preview_label)

        self._meta_label = Label("", "muted")
        self._meta_label.setWordWrap(True)
        self._meta_label.setStyleSheet(theme.panel_header_desc())
        right_layout.addWidget(self._meta_label)
        splitter.addWidget(right)

        splitter.setSizes([220, 400])
        layout.addWidget(splitter)
        self.setStyleSheet(theme.card_panel())

        self._rows: list[PipelineRow] = []
        self._cards: list[PosterCard] = []
        self._selected_index = -1

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._rows = list(rows)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        for i, r in enumerate(self._rows):
            card = PosterCard(
                title=r.tmdb_korean_title_group,
                meta=f"{r.year} • {r.season}",
                path="",
                image_url=r.poster_url,
            )
            card.setFixedHeight(80)
            card.setMinimumWidth(180)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = lambda e, idx=i: self._on_select(idx)
            self._list_layout.addWidget(card)
            self._cards.append(card)
        self._selected_index = -1
        if self._rows:
            self._on_select(0)

    def _on_select(self, index: int) -> None:
        self._selected_index = index
        r = self._rows[index]
        self._meta_label.setText(
            f"<b>원본 파일:</b> {r.original_file}<br>"
            f"<b>Parsed:</b> {r.parsed_title}<br>"
            f"<b>TMDB:</b> {r.tmdb_korean_title_group}<br>"
            f"<b>연도/시즌:</b> {r.year} / {r.season}<br>"
            f"<b>해상도:</b> {r.resolution}<br>"
            f"<b>경로:</b> {r.target_path}"
        )
        self.selection_changed.emit(index)
