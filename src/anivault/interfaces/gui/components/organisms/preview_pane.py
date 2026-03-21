"""Preview pane: right-side panel showing selected row poster."""

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import RoundedPixmapLabel
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow


class PreviewPane(QFrame):
    """Right pane: large poster image of selected PipelineRow."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(280)
        self.setMaximumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)

        self._img = RoundedPixmapLabel()
        self._img.setMinimumHeight(360)
        self._img.set_placeholder_text("항목을 선택하세요")
        layout.addWidget(self._img)

        self.setStyleSheet(theme.card_panel())

    def set_row(self, row: PipelineRow | PipelineGroupRow | None) -> None:
        if row is None:
            self._img.clear_source_pixmap()
            self._img.set_placeholder_text("항목을 선택하세요")
            return
        rep = row
        if isinstance(row, PipelineGroupRow):
            rep = row.representative()
            for m in row.members:
                if (m.tmdb_korean_title_group or "").strip():
                    rep = m
                    break
        # Poster loading is async elsewhere; for now show placeholder
        self._img.clear_source_pixmap()
        self._img.set_placeholder_text(f"Poster\n{rep.tmdb_korean_title_group}")

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self._img.set_source_pixmap(pixmap)
        else:
            self._img.clear_source_pixmap()
            self._img.set_placeholder_text("Poster")
