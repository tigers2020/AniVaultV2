"""settings_action_bar.py

Save / Reset / Load 버튼 바.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


class SettingsActionBar(QWidget):
    """설정 저장, 리셋, 불러오기 버튼 바."""

    save_clicked = Signal()
    reset_clicked = Signal()
    load_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.settings_row_gap_px())
        self._save_btn = Button(translate(K.SETTINGS_ACTION_SAVE), "primary")
        self._save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(self._save_btn)
        self._reset_btn = Button(translate(K.SETTINGS_ACTION_RESET))
        self._reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(self._reset_btn)
        self._load_btn = Button(translate(K.SETTINGS_ACTION_LOAD))
        self._load_btn.clicked.connect(self.load_clicked.emit)
        layout.addWidget(self._load_btn)
        layout.addStretch()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._save_btn.setText(translate(K.SETTINGS_ACTION_SAVE))
        self._reset_btn.setText(translate(K.SETTINGS_ACTION_RESET))
        self._load_btn.setText(translate(K.SETTINGS_ACTION_LOAD))
