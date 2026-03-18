"""Circular step index (1–6)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class StepIndex(QLabel):
    """Small circle with step number."""

    def __init__(self, index: int = 1, size: int = 24, parent=None):
        super().__init__(str(index), parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(theme.step_index_label())
        palette = self.palette()
        palette.setColor(palette.ColorRole.WindowText, QColor("#ffffff"))
        self.setPalette(palette)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(theme.COLORS["accent"]))
        grad.setColorAt(1, QColor(theme.COLORS["accent2"]))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        super().paintEvent(event)
