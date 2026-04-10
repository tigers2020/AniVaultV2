"""Topbar title and description."""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.i18n import translate
from anivault.interfaces.gui.i18n.keys import PAGE_ORGANIZER_DESC, PAGE_ORGANIZER_TITLE


class Topbar(QWidget):
    """Page title section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, theme.topbar_bottom_gap_px())
        left = QVBoxLayout()
        left.setSpacing(theme.panel_header_stack_gap_px())
        self._title = QLabel(translate(PAGE_ORGANIZER_TITLE))
        self._title.setStyleSheet(theme.topbar_title())
        left.addWidget(self._title)
        self._desc = QLabel(translate(PAGE_ORGANIZER_DESC))
        self._desc.setStyleSheet(theme.topbar_desc())
        self._desc.setWordWrap(True)
        left.addWidget(self._desc)
        layout.addLayout(left, 1)

    def set_page(self, title: str, description: str) -> None:
        self._title.setText(title)
        self._desc.setText(description)
