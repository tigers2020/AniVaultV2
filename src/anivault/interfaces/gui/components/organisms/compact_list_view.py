"""Compact list view: single column with thumbnail + title + meta per row."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.models import PipelineGroupRow


def _list_item_title(group: PipelineGroupRow) -> str:
    """Primary list label: parsed title first, then TMDB group title."""
    parsed = (group.parsed_title or "").strip()
    if parsed:
        return parsed
    tmdb = (group.tmdb_korean_title_group or "").strip()
    if tmdb:
        return tmdb
    rep = group.representative()
    base = (rep.parsed_title or "").strip()
    if base:
        return base
    if (rep.original_file or "").strip():
        return rep.original_file
    return "—"


def _list_item_meta(group: PipelineGroupRow) -> str:
    """Secondary line: file count and non-empty year / season / resolution."""
    parts: list[str] = []
    if len(group.members) > 1:
        parts.append(f"{len(group.members)}개 파일")
    for p in (group.year, group.season, group.resolution):
        s = (p or "").strip()
        if s:
            parts.append(s)
    return " • ".join(parts)


class _ListItem(QFrame):
    """Single row: small poster thumb + title + meta."""

    def __init__(self, group: PipelineGroupRow, parent: QWidget | None = None) -> None:
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
        title = Label(_list_item_title(group), "title")
        title.setStyleSheet(theme.list_item_strong())
        title.setWordWrap(True)
        right.addWidget(title)
        meta_text = _list_item_meta(group)
        meta = Label(meta_text, "muted")
        meta.setStyleSheet(theme.list_item_muted())
        meta.setVisible(bool(meta_text))
        right.addWidget(meta)
        layout.addLayout(right, 1)


class CompactListView(QFrame):
    """List view: compact rows with thumbnail + title."""

    selection_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
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

        self._groups: list[PipelineGroupRow] = []
        self._items: list[_ListItem] = []

    def set_rows(self, groups: list[PipelineGroupRow]) -> None:
        self._groups = list(groups)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()
        for i, g in enumerate(self._groups):
            w = _ListItem(g)
            w.setCursor(Qt.CursorShape.PointingHandCursor)
            w.mousePressEvent = lambda e, idx=i: self._on_click(idx)  # type: ignore[method-assign,misc]
            self._list_layout.addWidget(w)
            self._items.append(w)

    def _on_click(self, index: int) -> None:
        self.selection_changed.emit(index)
