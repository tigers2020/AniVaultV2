"""Compact list view: single column with thumbnail + title + meta per row."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.models import PipelineRow


class _ListItem(QFrame):
    """Single row: small poster thumb + title + meta."""

    def __init__(self, row: PipelineRow, parent=None):
        super().__init__(parent)
        self.setStyleSheet(theme.list_item())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Small thumbnail
        thumb = QLabel()
        thumb.setFixedSize(48, 72)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet(theme.poster_card_image())
        thumb.setText("—")
        layout.addWidget(thumb)
        self._thumb = thumb

        # Title + meta
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)
        title = Label(row.tmdb_korean_title_group, "title")
        title.setStyleSheet(theme.list_item_strong())
        title.setWordWrap(True)
        right.addWidget(title)
        meta = Label(f"{row.year} • {row.season} • {row.resolution}", "muted")
        meta.setStyleSheet(theme.list_item_muted())
        right.addWidget(meta)
        layout.addLayout(right, 1)


class CompactListView(QFrame):
    """List view: compact rows with thumbnail + title."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._list_layout = QVBoxLayout(container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        scroll.setWidget(container)

        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())

        self._rows: list[PipelineRow] = []
        self._items: list[_ListItem] = []

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._rows = list(rows)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()
        for i, r in enumerate(self._rows):
            w = _ListItem(r)
            w.setCursor(Qt.CursorShape.PointingHandCursor)
            w.mousePressEvent = lambda e, idx=i: self._on_click(idx)
            self._list_layout.addWidget(w)
            self._items.append(w)

    def _on_click(self, index: int) -> None:
        self.selection_changed.emit(index)
