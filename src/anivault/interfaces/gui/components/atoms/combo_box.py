"""Styled QComboBox."""

from PySide6.QtWidgets import QComboBox

from anivault.interfaces.gui import theme


class ComboBox(QComboBox):
    """Theme-backed combo box."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(theme.combo_box())
