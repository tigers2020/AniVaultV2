"""settings_action_bar.py

Save / Reset / Load 버튼 한 줄.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import Button


class SettingsActionBar(QWidget):
    """설정 저장·되돌리기·불러오기 시그널만보낸다."""

    save_clicked = Signal()
    reset_clicked = Signal()
    load_clicked = Signal()

    def __init__(self, parent=None):
        """버튼 행을 구성한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        save_btn = Button("Save", "primary")
        save_btn.clicked.connect(self.save_clicked.emit)
        layout.addWidget(save_btn)
        reset_btn = Button("Reset")
        reset_btn.clicked.connect(self.reset_clicked.emit)
        layout.addWidget(reset_btn)
        load_btn = Button("Load")
        load_btn.clicked.connect(self.load_clicked.emit)
        layout.addWidget(load_btn)
