"""Parse and TMDB rules form."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import ComboBox
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader

TMDB_MODES = [
    "Prefer TV and Korean localized title",
    "Prefer original title then localized fallback",
]


class ParseTmdbForm(QFrame):
    """Parse and TMDB rules panel fields."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader("Parse and TMDB Rules", "파일명 파싱과 TMDB 한글 제목 매핑 기준")
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        self._tmdb_api_key = FormField(
            "TMDB API key",
            "line",
            "Stored in .env as TMDB_API_KEY",
            echo_password=True,
        )
        self._ignore_tokens = FormField(
            "Ignore tokens", "line", "1080p, 720p, x264, WEBRip, BluRay, AAC, HEVC"
        )
        self._video_ext = FormField("Video extensions", "line", ".mkv, .mp4, .avi")
        lbl = QLabel("TMDB search mode")
        lbl.setStyleSheet(theme.form_label_muted())
        body.addWidget(lbl)
        self._tmdb_search = ComboBox()
        self._tmdb_search.addItems(TMDB_MODES)
        self._season_format = FormField("Season folder format", "line", "Season{season:02}")
        body.addWidget(self._tmdb_api_key)
        body.addWidget(self._ignore_tokens)
        body.addWidget(self._video_ext)
        body.addWidget(self._tmdb_search)
        body.addWidget(self._season_format)
        for f in (self._tmdb_api_key, self._ignore_tokens, self._video_ext, self._season_format):
            f.value_changed.connect(self.settings_changed.emit)
        self._tmdb_search.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def get_values(self) -> dict[str, str]:
        return {
            "tmdb_api_key": self._tmdb_api_key.value(),
            "ignore_tokens": self._ignore_tokens.value(),
            "video_extensions": self._video_ext.value(),
            "tmdb_search_mode": self._tmdb_search.currentText(),
            "season_folder_format": self._season_format.value(),
        }

    def set_values(self, data: dict[str, str]) -> None:
        self.blockSignals(True)
        try:
            if "tmdb_api_key" in data:
                self._tmdb_api_key.set_value(data["tmdb_api_key"])
            if "ignore_tokens" in data:
                self._ignore_tokens.set_value(data["ignore_tokens"])
            if "video_extensions" in data:
                self._video_ext.set_value(data["video_extensions"])
            if "tmdb_search_mode" in data:
                idx = self._tmdb_search.findText(data["tmdb_search_mode"])
                if idx >= 0:
                    self._tmdb_search.setCurrentIndex(idx)
            if "season_folder_format" in data:
                self._season_format.set_value(data["season_folder_format"])
        finally:
            self.blockSignals(False)
