"""Folder scan bar: PathSelectField + Scan button for Organizer page."""

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.components.molecules import PathSelectField


class FolderScanBar(QFrame):
    """PathSelectField + Scan button. Emits scan_clicked(path), path_changed(path)."""

    scan_clicked = Signal(str)
    match_clicked = Signal()
    path_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        self._path_field = PathSelectField(placeholder="스캔할 폴더 경로 (또는 폴더 선택 버튼)")
        self._path_field.path_changed.connect(self.path_changed.emit)
        layout.addWidget(self._path_field, 1)
        scan_btn = Button("스캔", "primary")
        scan_btn.clicked.connect(self._on_scan)
        layout.addWidget(scan_btn)
        match_btn = Button("TMDB 매칭")
        match_btn.clicked.connect(self.match_clicked.emit)
        layout.addWidget(match_btn)
        self.setStyleSheet(theme.card_panel())

        # Prevent vertical stretching when embedded in a resizable scroll area.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed))
        self._sync_fixed_height()

    def set_path(self, path: str) -> None:
        """Set path from settings. Synced with scan_build.source_path."""
        self._path_field.set_path(path)

    def _on_scan(self) -> None:
        path = self._path_field.path()
        self.scan_clicked.emit(path)

    def _sync_fixed_height(self) -> None:
        """Keep card height aligned to current font/style metrics."""
        h = int(self.layout().sizeHint().height()) if self.layout() is not None else 0
        if h <= 0:
            h = int(self.sizeHint().height())
        if h > 0:
            self.setFixedHeight(h)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_fixed_height()
