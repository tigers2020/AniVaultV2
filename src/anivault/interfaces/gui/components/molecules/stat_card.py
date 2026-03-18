"""Stat card: label + value (e.g. Scanned Files / 9,048)."""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label


class StatCard(QFrame):
    """Single stat: label on top, big value below."""

    def __init__(self, label_text: str, value: str = "0", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(6)
        lbl = Label(label_text, "stat")
        layout.addWidget(lbl)
        value_lbl = Label(value, "default")
        value_lbl.setStyleSheet(theme.stat_card_value())
        layout.addWidget(value_lbl)
        self.setStyleSheet(theme.stat_card())

    def set_value(self, value: str) -> None:
        layout = self.layout()
        if layout and layout.count() >= 2:
            w = layout.itemAt(1).widget()
            if w and hasattr(w, "setText"):
                w.setText(value)
