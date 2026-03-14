"""Topbar: page title + description + action buttons."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui import theme


class Topbar(QWidget):
    """Page title, subtitle, and top actions."""

    simulate_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 22)
        left = QVBoxLayout()
        left.setSpacing(6)
        self._title = QLabel("Organizer")
        self._title.setStyleSheet(theme.topbar_title())
        left.addWidget(self._title)
        self._desc = QLabel(
            "폴더 스캔부터 한글 제목 그룹 확정과 최종 경로 미리보기까지 한 화면에서 처리"
        )
        self._desc.setStyleSheet(theme.topbar_desc())
        self._desc.setWordWrap(True)
        left.addWidget(self._desc)
        layout.addLayout(left, 1)
        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(10)
        actions_layout.addWidget(Button("Load Preset"))
        actions_layout.addWidget(Button("Export Plan"))
        self._simulate_btn = Button("Simulate Pipeline", "primary")
        self._simulate_btn.clicked.connect(self.simulate_clicked.emit)
        actions_layout.addWidget(self._simulate_btn)
        layout.addWidget(actions)

    def set_page(self, title: str, description: str) -> None:
        self._title.setText(title)
        self._desc.setText(description)
