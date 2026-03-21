"""Image slot with pixmap clipped to a rounded rect (QLabel QSS cannot clip pixmap)."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget

from anivault.interfaces.gui import theme


class RoundedPixmapLabel(QWidget):
    """Fills a rounded rect with theme input_bg; draws pixmap clipped to that path, or placeholder text."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._source: QPixmap | None = None
        self._placeholder = ""
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    def set_placeholder_text(self, text: str) -> None:
        self._placeholder = text
        self.update()

    def placeholder_text(self) -> str:
        return self._placeholder

    def set_source_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self._source = pixmap
        else:
            self._source = None
        self.update()

    def clear_source_pixmap(self) -> None:
        self._source = None
        self.update()

    def _effective_radius(self) -> int:
        r = theme.frame_radius_px()
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return max(2, r)
        return max(2, min(r, w // 2, h // 2))

    def paintEvent(self, event) -> None:
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
