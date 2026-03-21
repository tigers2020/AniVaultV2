"""rounded_pixmap_label.py

QLabel QSS로는 못 하는 픽스맵 둥근 클리핑을 QPainter로 처리한다.

Author: Pom Kim
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from anivault.interfaces.gui import theme


class RoundedPixmapLabel(QWidget):
    """둥근 사각 슬롯에 픽스맵 또는 플레이스홀더 텍스트를 그린다."""

    def __init__(self, parent=None) -> None:
        """내부 소스·플레이스홀더를 초기화한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self._source: QPixmap | None = None
        self._placeholder = ""
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def set_placeholder_text(self, text: str) -> None:
        """플레이스홀더 문구를 바꾸고 다시 그린다.

        Args:
            self: 이 위젯.
            text: 이미지 없을 때 표시할 문자열.

        Returns:
            None.
        """
        self._placeholder = text
        self.update()

    def placeholder_text(self) -> str:
        """현재 플레이스홀더 문자열을 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            플레이스홀더.
        """
        return self._placeholder

    def set_source_pixmap(self, pixmap: QPixmap | None) -> None:
        """유효한 픽스맵이면 소스로 저장하고, 아니면 비운다.

        Args:
            self: 이 위젯.
            pixmap: 표시할 이미지. None 또는 null이면 클리어.

        Returns:
            None.
        """
        if pixmap is not None and not pixmap.isNull():
            self._source = pixmap
        else:
            self._source = None
        self.update()

    def clear_source_pixmap(self) -> None:
        """이미지 소스를 제거하고 다시 그린다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        self._source = None
        self.update()

    def _effective_radius(self) -> int:
        """위젯 크기에 맞춘 둥근 모서리 반경을 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            픽셀 반경(최소 2).
        """
        r = theme.frame_radius_px()
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return max(2, r)
        return max(2, min(r, w // 2, h // 2))

    def paintEvent(self, event) -> None:
        """배경·클리핑된 픽스맥 또는 플레이스홀더 텍스트를 그린다.

        Args:
            self: 이 위젯.
            event: 페인트 이벤트(미사용).

        Returns:
            None.
        """
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        r = self._effective_radius()
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), r, r)

        colors = theme.COLORS
        painter.fillPath(path, QColor(colors["input_bg"]))

        if self._source is not None and not self._source.isNull():
            painter.setClipPath(path)
            # Fill the slot (no letterboxing); clip removes overflow past rounded rect.
            scaled = self._source.scaled(
                rect.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = rect.x() + (rect.width() - scaled.width()) // 2
            y = rect.y() + (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            return

        painter.setPen(QColor(colors["muted"]))
        flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
        painter.drawText(rect, flags, self._placeholder)
