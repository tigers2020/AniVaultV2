"""Preview pane: right-side panel showing selected row poster."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.models import PipelineRow


class PreviewPane(QFrame):
    """Right pane: large poster image of selected PipelineRow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        self._img = QLabel()
        self._img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img.setMinimumHeight(360)
        self._img.setStyleSheet(theme.poster_card_image())
        self._img.setText("항목을 선택하세요")
        self._img.setScaledContents(False)
        layout.addWidget(self._img)

        self.setStyleSheet(theme.card_panel())

    def set_row(self, row: PipelineRow | None) -> None:
        if row is None:
            self._img.clear()
            self._img.setText("항목을 선택하세요")
            return
        # Poster loading is async elsewhere; for now show placeholder
        self._img.setText(f"Poster\n{row.tmdb_korean_title_group}")

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self._img.setPixmap(
                pixmap.scaled(
                    240,
                    360,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self._img.clear()
            self._img.setText("Poster")
