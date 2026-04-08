"""details_pane.py

Right-side details panel for the selected pipeline row or group.

Author: Pom Kim
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout

from anivault.constants.gui.components import (
    DETAILS_PANE_EMPTY_STATE,
    DETAILS_PANE_GROUP_FILES_LABEL,
    DETAILS_PANE_MANUAL_MATCH_BUTTON,
    DETAILS_PANE_MEMBER_META_JOINER,
    DETAILS_PANE_ORIGINAL_FILE_LABEL,
    DETAILS_PANE_PARSE_GROUP_LABEL,
    DETAILS_PANE_PARSED_TITLE_LABEL,
    DETAILS_PANE_RESOLUTION_LABEL,
    DETAILS_PANE_STATUS_LABEL,
    DETAILS_PANE_TARGET_PATH_LABEL,
    DETAILS_PANE_TMDB_TITLE_LABEL,
    DETAILS_PANE_YEAR_SEASON_EP_LABEL,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow


def _member_lines(group: PipelineGroupRow) -> str:
    parts: list[str] = []
    for member in group.members:
        name = Path(member.original_file).name
        extra = DETAILS_PANE_MEMBER_META_JOINER.join(
            part
            for part in (
                member.season or "",
                member.episode or "",
                member.resolution or "",
            )
            if (part or "").strip()
        )
        if extra:
            parts.append(f"{name}<br><small>{extra}</small>")
        else:
            parts.append(name)
    return "<br>".join(parts)


class DetailsPane(QFrame):
    """HTML details panel for the selected file or group."""

    manual_match_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self.setMaximumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QLabel()
        self._content.setWordWrap(True)
        self._content.setText(DETAILS_PANE_EMPTY_STATE)
        self._content.setStyleSheet(theme.panel_header_desc())
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        self._manual_btn = Button(DETAILS_PANE_MANUAL_MATCH_BUTTON, "default")
        self._manual_btn.setEnabled(False)
        self._manual_btn.clicked.connect(self.manual_match_requested.emit)
        layout.addWidget(self._manual_btn)

        self.setStyleSheet(theme.card_panel())

    def set_row(self, row: PipelineRow | PipelineGroupRow | None) -> None:
        if row is None:
            self._content.setText(DETAILS_PANE_EMPTY_STATE)
            self._manual_btn.setEnabled(False)
            return

        self._manual_btn.setEnabled(True)
        if isinstance(row, PipelineGroupRow):
            if len(row.members) > 1:
                files_block = _member_lines(row)
                self._content.setText(
                    f"<b>{DETAILS_PANE_GROUP_FILES_LABEL} ({len(row.members)}개)</b><br>{files_block}<br><br>"
                    f"<b>{DETAILS_PANE_PARSED_TITLE_LABEL}</b><br>{row.parsed_title}<br><br>"
                    f"<b>{DETAILS_PANE_PARSE_GROUP_LABEL}</b><br>{row.parse_group}<br><br>"
                    f"<b>{DETAILS_PANE_TMDB_TITLE_LABEL}</b><br>{row.tmdb_korean_title_group}<br><br>"
                    f"<b>{DETAILS_PANE_YEAR_SEASON_EP_LABEL}</b><br>{row.year} / {row.season} / {row.episode}<br><br>"
                    f"<b>{DETAILS_PANE_RESOLUTION_LABEL}</b><br>{row.resolution}<br><br>"
                    f"<b>{DETAILS_PANE_STATUS_LABEL}</b><br>{row.status}<br><br>"
                    f"<b>{DETAILS_PANE_TARGET_PATH_LABEL}</b><br>{row.target_path}"
                )
            else:
                self._set_single_row(row.representative())
            return

        self._set_single_row(row)

    def _set_single_row(self, row: PipelineRow) -> None:
        self._content.setText(
            f"<b>{DETAILS_PANE_ORIGINAL_FILE_LABEL}</b><br>{row.original_file}<br><br>"
            f"<b>{DETAILS_PANE_PARSED_TITLE_LABEL}</b><br>{row.parsed_title}<br><br>"
            f"<b>{DETAILS_PANE_PARSE_GROUP_LABEL}</b><br>{row.parse_group}<br><br>"
            f"<b>{DETAILS_PANE_TMDB_TITLE_LABEL}</b><br>{row.tmdb_korean_title_group}<br><br>"
            f"<b>{DETAILS_PANE_YEAR_SEASON_EP_LABEL}</b><br>{row.year} / {row.season} / {row.episode}<br><br>"
            f"<b>{DETAILS_PANE_RESOLUTION_LABEL}</b><br>{row.resolution}<br><br>"
            f"<b>{DETAILS_PANE_STATUS_LABEL}</b><br>{row.status}<br><br>"
            f"<b>{DETAILS_PANE_TARGET_PATH_LABEL}</b><br>{row.target_path}"
        )
