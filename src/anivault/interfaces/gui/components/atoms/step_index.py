"""step_index.py

원형 배경에 단계 번호(1–6 등)를 표시하는 QLabel.

Author: Pom Kim
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class StepIndex(QLabel):
    """그라데이션 원과 흰색 숫자 라벨."""

    def __init__(self, index: int = 1, size: int = 24, parent=None):
        """단계 번호와 원 크기를 설정한다.

        Args:
            self: 이 위젯.
            index: 표시할 정수(문자열로 변환).
            size: 정사각형 한 변 픽셀.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(str(index), parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(theme.step_index_label())
        palette = self.palette()
        palette.setColor(palette.ColorRole.WindowText, QColor("#ffffff"))
        self.setPalette(palette)

    def paintEvent(self, event: QPaintEvent) -> None:
        """그라데이션 원을 그린 뒤 기본 라벨 페인트를 호출한다.

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
        painter.drawEllipse(self.rect())
        super().paintEvent(event)
