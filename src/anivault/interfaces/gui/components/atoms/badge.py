"""Brand logo badge (e.g. 'A' for AniVault)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QLabel

from anivault.interfaces.gui import theme


class Badge(QFrame):
    """Fixed-size badge with gradient background and single character."""

    def __init__(self, text: str = "A", size: int = 42, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._label = QLabel(text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(theme.badge_label(size))
        self._label.setGeometry(0, 0, size, size)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(theme.COLORS["accent"]))
        grad.setColorAt(1, QColor(theme.COLORS["accent2"]))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        super().paintEvent(event)
