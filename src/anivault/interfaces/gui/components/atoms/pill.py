"""Status pill (blue, green, yellow, red)."""

from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class Pill(QLabel):
    """Small status chip. color: 'blue' | 'green' | 'yellow' | 'red'."""

    def __init__(self, text: str = "", color: str = "blue", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(theme.pill(color))
