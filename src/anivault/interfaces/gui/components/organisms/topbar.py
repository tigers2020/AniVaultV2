"""Topbar title and description."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.constants.gui.copy import TOPBAR_DEFAULT_DESCRIPTION, TOPBAR_DEFAULT_TITLE
from anivault.interfaces.gui import theme


class Topbar(QWidget):
    """Page title section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, theme.topbar_bottom_gap_px())
        left = QVBoxLayout()
        left.setSpacing(theme.panel_header_stack_gap_px())
        self._title = QLabel(TOPBAR_DEFAULT_TITLE)
        self._title.setStyleSheet(theme.topbar_title())
        left.addWidget(self._title)
        self._desc = QLabel(TOPBAR_DEFAULT_DESCRIPTION)
        self._desc.setStyleSheet(theme.topbar_desc())
        self._desc.setWordWrap(True)
        left.addWidget(self._desc)
        layout.addLayout(left, 1)

    def set_page(self, title: str, description: str) -> None:
        self._title.setText(title)
        self._desc.setText(description)
