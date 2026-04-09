"""parse_tmdb_form.py

파일명 파싱과 TMDB 검색 규칙 설정 폼.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.constants.gui.components import (
    PARSE_TMDB_FORM_API_KEY_HELP,
    PARSE_TMDB_FORM_HEADER_DESCRIPTION,
    PARSE_TMDB_FORM_HEADER_TITLE,
    PARSE_TMDB_FORM_LABEL_API_KEY,
    PARSE_TMDB_FORM_LABEL_IGNORE_TOKENS,
    PARSE_TMDB_FORM_LABEL_SEASON_FORMAT,
)
from anivault.constants.gui.settings import DEFAULT_PARSE_TMDB
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader


class ParseTmdbForm(QFrame):
    """Parse/TMDB 규칙 입력 폼."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(PARSE_TMDB_FORM_HEADER_TITLE, PARSE_TMDB_FORM_HEADER_DESCRIPTION)
        )
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._tmdb_api_key = FormField(
            PARSE_TMDB_FORM_LABEL_API_KEY,
            "line",
            PARSE_TMDB_FORM_API_KEY_HELP,
            echo_password=True,
        )
        self._ignore_tokens = FormField(
            PARSE_TMDB_FORM_LABEL_IGNORE_TOKENS,
            "line",
            str(DEFAULT_PARSE_TMDB["ignore_tokens"]),
        )
        self._season_format = FormField(
            PARSE_TMDB_FORM_LABEL_SEASON_FORMAT,
            "line",
            str(DEFAULT_PARSE_TMDB["season_folder_format"]),
        )
        body.addWidget(self._tmdb_api_key)
        body.addWidget(self._ignore_tokens)
        body.addWidget(self._season_format)
        for field in (
            self._tmdb_api_key,
            self._ignore_tokens,
            self._season_format,
        ):
            field.value_changed.connect(self.settings_changed.emit)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def get_values(self) -> dict[str, str]:
        return {
            "tmdb_api_key": self._tmdb_api_key.value(),
            "ignore_tokens": self._ignore_tokens.value(),
            "season_folder_format": self._season_format.value(),
        }

    def set_values(self, data: dict[str, str]) -> None:
        self.blockSignals(True)
        try:
            if "tmdb_api_key" in data:
                self._tmdb_api_key.set_value(data["tmdb_api_key"])
            if "ignore_tokens" in data:
                self._ignore_tokens.set_value(data["ignore_tokens"])
            if "season_folder_format" in data:
                self._season_format.set_value(data["season_folder_format"])
        finally:
            self.blockSignals(False)
