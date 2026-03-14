"""Parse and TMDB rules form."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

from anivault.interfaces.gui.components.molecules import PanelHeader, FormField
from anivault.interfaces.gui.components.atoms import ComboBox
from anivault.interfaces.gui import theme


class ParseTmdbForm(QFrame):
    """Parse and TMDB rules panel fields."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader("Parse and TMDB Rules", "파일명 파싱과 TMDB 한글 제목 매핑 기준")
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        body.addWidget(FormField("Ignore tokens", "line", "1080p, 720p, x264, WEBRip, BluRay, AAC, HEVC"))
        body.addWidget(FormField("Video extensions", "line", ".mkv, .mp4, .avi"))
        lbl = QLabel("TMDB search mode")
        lbl.setStyleSheet(theme.form_label_muted())
        body.addWidget(lbl)
        self._tmdb_search = ComboBox()
        self._tmdb_search.addItems([
            "Prefer TV and Korean localized title",
            "Prefer original title then localized fallback",
        ])
        body.addWidget(self._tmdb_search)
        body.addWidget(FormField("Season folder format", "line", "Season{season:02}"))
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
