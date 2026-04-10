"""details_pane.py

Right-side details panel for the selected pipeline row or group.

Author: Pom Kim
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n.pipeline_status import translate_pipeline_status
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow


class DetailsPane(QFrame):
    """HTML details panel for the selected file or group."""

    manual_match_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_row: PipelineRow | PipelineGroupRow | None = None
        self.setMinimumWidth(theme.details_pane_min_width_px())
        self.setMaximumWidth(theme.details_pane_max_width_px())
        layout = QVBoxLayout(self)
        body_padding = theme.card_body_padding_px()
        layout.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        layout.setSpacing(theme.inline_control_gap_px())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QLabel()
        self._content.setWordWrap(True)
        self._content.setText(translate(K.DETAILS_EMPTY))
        self._content.setStyleSheet(theme.panel_header_desc())
        scroll.setWidget(self._content)
        layout.addWidget(scroll)

        self._manual_btn = Button(translate(K.DETAILS_MANUAL_BTN), "default")
        self._manual_btn.setEnabled(False)
        self._manual_btn.clicked.connect(self.manual_match_requested.emit)
        layout.addWidget(self._manual_btn)

        self.setStyleSheet(theme.card_panel())
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._manual_btn.setText(translate(K.DETAILS_MANUAL_BTN))
        self.set_row(self._current_row)

    def _joiner(self) -> str:
        return translate(K.DETAILS_JOINER)

    def _member_lines(self, group: PipelineGroupRow) -> str:
        parts: list[str] = []
        j = self._joiner()
        for member in group.members:
            name = Path(member.original_file).name
            extra = j.join(
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

    def _group_files_heading(self, n: int) -> str:
        unit = translate(K.CONTENT_FILE_COUNT_INLINE).format(count=n)
        return f"<b>{translate(K.DETAILS_LBL_GROUP_FILES)} {unit}</b>"

    def _html_group_multi(self, row: PipelineGroupRow) -> str:
        files_block = self._member_lines(row)
        st = translate_pipeline_status(str(row.status or ""))
        return (
            f"{self._group_files_heading(len(row.members))}<br>{files_block}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_PARSED)}</b><br>{row.parsed_title}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_PARSE_GROUP)}</b><br>{row.parse_group}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_TMDB)}</b><br>{row.tmdb_korean_title_group}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_YEAR_SEASON_EP)}</b><br>"
            f"{row.year} / {row.season} / {row.episode}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_RESOLUTION)}</b><br>{row.resolution}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_STATUS)}</b><br>{st}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_TARGET)}</b><br>{row.target_path}"
        )

    def _html_single(self, row: PipelineRow) -> str:
        st = translate_pipeline_status(str(row.status or ""))
        return (
            f"<b>{translate(K.DETAILS_LBL_ORIGINAL)}</b><br>{row.original_file}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_PARSED)}</b><br>{row.parsed_title}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_PARSE_GROUP)}</b><br>{row.parse_group}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_TMDB)}</b><br>{row.tmdb_korean_title_group}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_YEAR_SEASON_EP)}</b><br>"
            f"{row.year} / {row.season} / {row.episode}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_RESOLUTION)}</b><br>{row.resolution}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_STATUS)}</b><br>{st}<br><br>"
            f"<b>{translate(K.DETAILS_LBL_TARGET)}</b><br>{row.target_path}"
        )

    def set_row(self, row: PipelineRow | PipelineGroupRow | None) -> None:
        self._current_row = row
        if row is None:
            self._content.setText(translate(K.DETAILS_EMPTY))
            self._manual_btn.setEnabled(False)
            return

        self._manual_btn.setEnabled(True)
        if isinstance(row, PipelineGroupRow):
            if len(row.members) > 1:
                self._content.setText(self._html_group_multi(row))
            else:
                self._content.setText(self._html_single(row.representative()))
            return

        self._content.setText(self._html_single(row))
