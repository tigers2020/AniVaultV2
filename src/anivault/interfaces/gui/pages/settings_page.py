"""Settings page: ScanBuildCard + PathRulesForm + ParseTmdbForm (organisms only)."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import (
    ScanBuildCard,
    PathRulesForm,
    ParseTmdbForm,
)


class SettingsPage(QWidget):
    """Settings: scan/build card + path rules + parse/TMDB rules (organisms only)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(ScanBuildCard())
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(18)
        settings_layout.addWidget(PathRulesForm(), 12)
        settings_layout.addWidget(ParseTmdbForm(), 8)
        content_layout.addLayout(settings_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
