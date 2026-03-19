"""Settings page: AppearanceCard + ScanBuildCard + PathRulesForm + ParseTmdbForm."""

from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.organisms import (
    AppearanceCard,
    ParseTmdbForm,
    PathRulesForm,
    ScanBuildCard,
    SettingsActionsCard,
)
from anivault.interfaces.gui.presenters import SettingsPresenter


class SettingsPage(QWidget):
    """Settings: appearance + scan/build + path rules + parse/TMDB rules."""

    def __init__(self, parent=None, presenter: SettingsPresenter | None = None):
        super().__init__(parent)
        self._presenter = presenter if presenter is not None else SettingsPresenter(parent=self)
        if presenter is not None:
            self._presenter.setParent(self)
        scan_card = ScanBuildCard()
        scan_card.scan_clicked.connect(self._presenter.on_scan_clicked)
        appearance_card = AppearanceCard()
        appearance_card.theme_changed.connect(self._presenter.on_theme_changed)
        path_rules_form = PathRulesForm()
        parse_tmdb_form = ParseTmdbForm()
        self._presenter.set_forms(path_rules_form, parse_tmdb_form, scan_card)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        actions_card = SettingsActionsCard()
        bar = actions_card.action_bar()
        bar.save_clicked.connect(self._presenter.on_save_clicked)
        bar.reset_clicked.connect(self._presenter.on_reset_clicked)
        bar.load_clicked.connect(self._presenter.on_load_clicked)
        content_layout.addWidget(actions_card)
        content_layout.addWidget(appearance_card)
        content_layout.addWidget(scan_card)
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(18)
        settings_layout.addWidget(path_rules_form, 12)
        settings_layout.addWidget(parse_tmdb_form, 8)
        content_layout.addLayout(settings_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
