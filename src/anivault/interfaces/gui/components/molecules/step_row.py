"""Step row: StepIndex + description text."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from anivault.interfaces.gui.components.atoms import StepIndex
from anivault.interfaces.gui import theme


class StepRow(QWidget):
    """Single pipeline step: number circle + text."""

    def __init__(self, index: int, title: str, description: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(StepIndex(index, 24))
        text = QLabel(f"<b>{title}</b><br/>{description}" if description else title)
        text.setStyleSheet(theme.step_row_text())
        text.setWordWrap(True)
        layout.addWidget(text, 1)
