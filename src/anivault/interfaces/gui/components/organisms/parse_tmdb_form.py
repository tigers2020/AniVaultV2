"""parse_tmdb_form.py

파일명 파싱과 TMDB 검색 규칙 설정 폼.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.constants.gui.settings import DEFAULT_PARSE_TMDB
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


class ParseTmdbForm(QFrame):
    """Parse/TMDB 규칙 입력 폼."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._header = PanelHeader(
            translate(K.SETTINGS_PARSE_TITLE),
            translate(K.SETTINGS_PARSE_DESC),
        )
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._tmdb_api_key = FormField(
            translate(K.SETTINGS_PARSE_LBL_API),
            "line",
            translate(K.SETTINGS_PARSE_API_HELP),
            echo_password=True,
        )
        self._ignore_tokens = FormField(
            translate(K.SETTINGS_PARSE_LBL_IGNORE),
            "line",
            str(DEFAULT_PARSE_TMDB["ignore_tokens"]),
        )
        self._season_format = FormField(
            translate(K.SETTINGS_PARSE_LBL_SEASON),
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
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(K.SETTINGS_PARSE_TITLE),
            translate(K.SETTINGS_PARSE_DESC),
        )
        self._tmdb_api_key.apply_static_label(translate(K.SETTINGS_PARSE_LBL_API))
        self._ignore_tokens.apply_static_label(translate(K.SETTINGS_PARSE_LBL_IGNORE))
        self._season_format.apply_static_label(translate(K.SETTINGS_PARSE_LBL_SEASON))

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
