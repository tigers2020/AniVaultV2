"""Step row: StepIndex + description text."""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import StepIndex


def _apply_text_color(label: QLabel) -> None:
    """Ensure label text color via palette (fixes dark theme HTML/rich-text issues)."""
    palette = label.palette()
    palette.setColor(palette.ColorRole.WindowText, QColor(theme.COLORS["text"]))
    label.setPalette(palette)


class StepRow(QWidget):
    """Single pipeline step: number circle + text."""

    def __init__(self, index: int, title: str, description: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.addWidget(StepIndex(index, 24))
        text_wrapper = QWidget()
        text_layout = QVBoxLayout(text_wrapper)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(theme.step_row_title())
        title_lbl.setWordWrap(True)
        _apply_text_color(title_lbl)
        text_layout.addWidget(title_lbl)
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(theme.step_row_text())
            desc_lbl.setWordWrap(True)
            _apply_text_color(desc_lbl)
            text_layout.addWidget(desc_lbl)
        layout.addWidget(text_wrapper, 1)
