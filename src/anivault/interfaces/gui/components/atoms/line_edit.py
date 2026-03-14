"""Styled QLineEdit."""

from PySide6.QtWidgets import QLineEdit

from anivault.interfaces.gui import theme


class LineEdit(QLineEdit):
    """Theme-backed line edit."""

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(text or "")
        self.setStyleSheet(theme.line_edit())
