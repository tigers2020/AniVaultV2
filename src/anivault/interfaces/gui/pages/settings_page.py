"""settings_page.py

설정 카드 그리드: 외형·스캔·경로·파서·저장 액션.

Author: Pom Kim
"""

from PySide6.QtWidgets import QGridLayout, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.organisms import (
    AppearanceCard,
    ParseTmdbForm,
    PathRulesForm,
    ScanBuildCard,
    SettingsActionsCard,
)
from anivault.interfaces.gui.presenters import SettingsPresenter


class SettingsPage(QWidget):
    """Appearance, ScanBuild, PathRules, ParseTmdb, Actions."""

    def __init__(self, parent=None, presenter: SettingsPresenter | None = None):
        """Presenter와 폼·시그널을 연결한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).
            presenter: SettingsPresenter. None이면 자체 생성.

        Returns:
            None.
        """
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
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        actions_card = SettingsActionsCard()
        bar = actions_card.action_bar()
        bar.save_clicked.connect(self._presenter.on_save_clicked)
        bar.reset_clicked.connect(self._presenter.on_reset_clicked)
        bar.load_clicked.connect(self._presenter.on_load_clicked)
        settings_grid = QGridLayout()
        settings_grid.setContentsMargins(0, 0, 0, 0)
        settings_grid.setHorizontalSpacing(14)
        settings_grid.setVerticalSpacing(14)
        settings_grid.setColumnStretch(0, 11)
        settings_grid.setColumnStretch(1, 9)
        settings_grid.addWidget(actions_card, 0, 0)
        settings_grid.addWidget(appearance_card, 0, 1)
        settings_grid.addWidget(scan_card, 1, 0, 1, 2)
        settings_grid.addWidget(path_rules_form, 2, 0)
        settings_grid.addWidget(parse_tmdb_form, 2, 1)
        content_layout.addLayout(settings_grid)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll)
