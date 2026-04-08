"""badge.py

브랜드 로고용 단일 문자 배지(예: AniVault 'A').

Author: Pom Kim
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QFrame, QLabel

from anivault.interfaces.gui import theme


class Badge(QFrame):
    """고정 크기·그라데이션 배경·한 글자 라벨."""

    def __init__(self, text: str = "A", size: int = 42, parent=None):
        """배지 문자와 한 변 길이를 설정한다.

        Args:
            self: 이 위젯.
            text: 중앙 글자.
            size: 정사각형 한 변 픽셀.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._label = QLabel(text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(theme.badge_label(size))
        self._label.setGeometry(0, 0, size, size)

    def paintEvent(self, arg__1: QPaintEvent) -> None:
        """둥근 사각 그라데이션 배경을 그린 뒤 기본 페인트를 호출한다.

        Args:
            self: 이 위젯.
            event: Qt 페인트 이벤트.

        Returns:
            None.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, QColor(theme.COLORS["accent"]))
        grad.setColorAt(1, QColor(theme.COLORS["accent2"]))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)
        super().paintEvent(arg__1)
