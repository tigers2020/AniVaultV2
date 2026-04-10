"""Split content view with a poster-card list and metadata panel."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QScrollArea, QSplitter, QVBoxLayout, QWidget

from anivault.constants.gui.components import (
    CONTENT_VIEW_GROUP_FILES_LABEL,
    CONTENT_VIEW_META_JOINER,
    CONTENT_VIEW_MULTI_FILE_SUFFIX,
    CONTENT_VIEW_ORIGINAL_FILE_LABEL,
    CONTENT_VIEW_PARSED_LABEL,
    CONTENT_VIEW_PATH_LABEL,
    CONTENT_VIEW_RESOLUTION_LABEL,
    CONTENT_VIEW_TMDB_LABEL,
    CONTENT_VIEW_YEAR_SEASON_LABEL,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.models import PipelineGroupRow, pipeline_group_display_image_url


class ContentView(QFrame):
    """Left poster-card list plus right metadata content area."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QFrame()
        left.setMinimumWidth(theme.result_list_panel_min_width_px())
        left.setMaximumWidth(theme.result_list_panel_max_width_px())
        left.setStyleSheet(theme.card_panel())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet(theme.scroll_area_transparent())
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        card_padding = theme.card_body_padding_px()
        self._list_layout.setContentsMargins(
            card_padding,
            card_padding,
            card_padding,
            card_padding,
        )
        self._list_layout.setSpacing(theme.compact_gap_px())
        left_scroll.setWidget(self._list_container)
        left_layout.addWidget(left_scroll)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(theme.scroll_area_transparent())
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._meta_scroll_content = QWidget()
        meta_content_layout = QVBoxLayout(self._meta_scroll_content)
        meta_padding = theme.card_body_padding_px()
        meta_content_layout.setContentsMargins(
            meta_padding, meta_padding, meta_padding, meta_padding
        )
        meta_content_layout.setSpacing(theme.compact_gap_px())

        self._meta_frame = QFrame()
        self._meta_frame.setObjectName("content_view_text_panel")
        self._meta_frame.setStyleSheet(theme.content_view_text_panel_overlay())
        meta_layout = QVBoxLayout(self._meta_frame)
        meta_layout.setContentsMargins(meta_padding, meta_padding, meta_padding, meta_padding)
        self._meta_label = Label("", "muted")
        self._meta_label.setWordWrap(True)
        self._meta_label.setStyleSheet(theme.panel_header_desc())
        meta_layout.addWidget(self._meta_label)
        meta_content_layout.addWidget(self._meta_frame)
        meta_content_layout.addStretch(1)

        right_scroll.setWidget(self._meta_scroll_content)
        right_layout.addWidget(right_scroll)
        splitter.addWidget(right)

        splitter.setSizes(
            [
                theme.result_list_panel_min_width_px(),
                theme.result_splitter_main_width_px(),
            ]
        )
        layout.addWidget(splitter)
        self.setStyleSheet(theme.card_panel())

        self._groups: list[PipelineGroupRow] = []
        self._cards: list[PosterCard] = []
        self._selected_index = -1

    def poster_cards(self) -> list[PosterCard]:
        return list(self._cards)

    def _clear_list_widgets(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _compact_meta_for_group(group: PipelineGroupRow) -> str:
        meta_parts: list[str] = []
        if len(group.members) > 1:
            meta_parts.append(f"{len(group.members)}{CONTENT_VIEW_MULTI_FILE_SUFFIX}")
        for part in (group.year, group.season, group.resolution):
            value = (part or "").strip()
            if value:
                meta_parts.append(value)
        return CONTENT_VIEW_META_JOINER.join(meta_parts)

    @staticmethod
    def _group_card_title(group: PipelineGroupRow) -> str:
        return (group.tmdb_korean_title_group or "").strip() or (group.parsed_title or "").strip()

    def _add_group_card(self, index: int, group: PipelineGroupRow) -> None:
        card = PosterCard(
            title=self._group_card_title(group),
            meta=self._compact_meta_for_group(group),
            path="",
            image_url=pipeline_group_display_image_url(group),
            variant="compact",
            image_aspect="backdrop",
            text_panel_overlay=True,
        )
        card.setMinimumWidth(theme.result_list_panel_min_width_px() - theme.card_body_padding_px())
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda event, idx=index: self._on_select(idx)  # type: ignore[method-assign,misc]
        self._list_layout.addWidget(card)
        self._cards.append(card)

    def set_rows(self, groups: list[PipelineGroupRow]) -> None:
        self._groups = list(groups)
        self._clear_list_widgets()
        self._cards.clear()
        for index, group in enumerate(self._groups):
            self._add_group_card(index, group)
        self._selected_index = -1
        if self._groups:
            self._on_select(0)

    @staticmethod
    def _meta_html_for_group(group: PipelineGroupRow) -> str:
        if len(group.members) > 1:
            files_html = "<br>".join(Path(member.original_file).name for member in group.members)
            return (
                f"<b>{CONTENT_VIEW_GROUP_FILES_LABEL} ({len(group.members)}개)</b><br>{files_html}<br><br>"
                f"<b>{CONTENT_VIEW_PARSED_LABEL}:</b> {group.parsed_title}<br>"
                f"<b>{CONTENT_VIEW_TMDB_LABEL}:</b> {group.tmdb_korean_title_group}<br>"
                f"<b>{CONTENT_VIEW_YEAR_SEASON_LABEL}:</b> {group.year} / {group.season}<br>"
                f"<b>{CONTENT_VIEW_RESOLUTION_LABEL}:</b> {group.resolution}<br>"
                f"<b>{CONTENT_VIEW_PATH_LABEL}:</b> {group.target_path}"
            )
        row = group.representative()
        return (
            f"<b>{CONTENT_VIEW_ORIGINAL_FILE_LABEL}:</b> {row.original_file}<br>"
            f"<b>{CONTENT_VIEW_PARSED_LABEL}:</b> {row.parsed_title}<br>"
            f"<b>{CONTENT_VIEW_TMDB_LABEL}:</b> {row.tmdb_korean_title_group}<br>"
            f"<b>{CONTENT_VIEW_YEAR_SEASON_LABEL}:</b> {row.year} / {row.season}<br>"
            f"<b>{CONTENT_VIEW_RESOLUTION_LABEL}:</b> {row.resolution}<br>"
            f"<b>{CONTENT_VIEW_PATH_LABEL}:</b> {row.target_path}"
        )

    def _on_select(self, index: int) -> None:
        self._selected_index = index
        group = self._groups[index]
        self._meta_label.setText(self._meta_html_for_group(group))
        self.selection_changed.emit(index)
