"""settings_action_bar.py

Save / Reset / Load 버튼 바.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.constants.gui.components import (
    SETTINGS_ACTION_BAR_BUTTON_LOAD,
    SETTINGS_ACTION_BAR_BUTTON_RESET,
    SETTINGS_ACTION_BAR_BUTTON_SAVE,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button


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
        save_btn = Button(SETTINGS_ACTION_BAR_BUTTON_SAVE, "primary")
        save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(save_btn)
        reset_btn = Button(SETTINGS_ACTION_BAR_BUTTON_RESET)
        reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(reset_btn)
        load_btn = Button(SETTINGS_ACTION_BAR_BUTTON_LOAD)
        load_btn.clicked.connect(self.load_clicked.emit)
        layout.addWidget(load_btn)
        layout.addStretch()
