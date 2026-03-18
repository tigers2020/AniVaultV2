"""Settings page: ScanBuildCard + PathRulesForm + ParseTmdbForm (organisms only)."""

from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import (
    ParseTmdbForm,
    PathRulesForm,
    ScanBuildCard,
)
from anivault.interfaces.gui.presenters import SettingsPresenter


class SettingsPage(QWidget):
    """Settings: scan/build card + path rules + parse/TMDB rules (organisms only)."""

    def __init__(self, parent=None, presenter: SettingsPresenter | None = None):
        super().__init__(parent)
        self._presenter = presenter if presenter is not None else SettingsPresenter(parent=self)
        if presenter is not None:
            self._presenter.setParent(self)
        scan_card = ScanBuildCard()
        scan_card.scan_clicked.connect(self._presenter.on_scan_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(scan_card)
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(18)
        settings_layout.addWidget(PathRulesForm(), 12)
        settings_layout.addWidget(ParseTmdbForm(), 8)
        content_layout.addLayout(settings_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
