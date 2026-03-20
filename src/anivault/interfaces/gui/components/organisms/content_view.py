"""Content view: top = large preview of selected, bottom = metadata. List on left."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.models import PipelineGroupRow


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
        left.setMinimumWidth(260)
        left.setMaximumWidth(420)
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
        self._preview_label.setMinimumHeight(300)
        self._preview_label.setStyleSheet(theme.poster_card_image())
        self._preview_label.setText("항목을 선택하세요")
        self._preview_label.setScaledContents(False)
        right_layout.addWidget(self._preview_label)

        self._meta_label = Label("", "muted")
        self._meta_label.setWordWrap(True)
        self._meta_label.setStyleSheet(theme.panel_header_desc())
        right_layout.addWidget(self._meta_label)
        splitter.addWidget(right)

        splitter.setSizes([320, 900])
        layout.addWidget(splitter)
        self.setStyleSheet(theme.card_panel())

        self._groups: list[PipelineGroupRow] = []
        self._cards: list[PosterCard] = []
        self._selected_index = -1

    def set_rows(self, groups: list[PipelineGroupRow]) -> None:
        self._groups = list(groups)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        for i, g in enumerate(self._groups):
            title = (g.tmdb_korean_title_group or "").strip() or (g.parsed_title or "").strip()
            meta_parts = [p for p in (g.year, g.season) if (p or "").strip()]
            if len(g.members) > 1:
                meta_parts.insert(0, f"{len(g.members)}개 파일")
            meta = " • ".join(meta_parts)
            card = PosterCard(
                title=title,
                meta=meta,
                path="",
                image_url=g.poster_url,
                variant="compact",
            )
            card.setFixedHeight(92)
            card.setMinimumWidth(220)
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = lambda e, idx=i: self._on_select(idx)  # type: ignore[method-assign,misc]
            self._list_layout.addWidget(card)
            self._cards.append(card)
        self._selected_index = -1
        if self._groups:
            self._on_select(0)

    def _on_select(self, index: int) -> None:
        self._selected_index = index
        g = self._groups[index]
        if len(g.members) > 1:
            files_html = "<br>".join(Path(m.original_file).name for m in g.members)
            self._meta_label.setText(
                f"<b>파일 ({len(g.members)}개)</b><br>{files_html}<br><br>"
                f"<b>Parsed:</b> {g.parsed_title}<br>"
                f"<b>TMDB:</b> {g.tmdb_korean_title_group}<br>"
                f"<b>연도/시즌:</b> {g.year} / {g.season}<br>"
                f"<b>해상도:</b> {g.resolution}<br>"
                f"<b>경로:</b> {g.target_path}"
            )
        else:
            r = g.members[0]
            self._meta_label.setText(
                f"<b>원본 파일:</b> {r.original_file}<br>"
                f"<b>Parsed:</b> {r.parsed_title}<br>"
                f"<b>TMDB:</b> {r.tmdb_korean_title_group}<br>"
                f"<b>연도/시즌:</b> {r.year} / {r.season}<br>"
                f"<b>해상도:</b> {r.resolution}<br>"
                f"<b>경로:</b> {r.target_path}"
            )
        self.selection_changed.emit(index)
