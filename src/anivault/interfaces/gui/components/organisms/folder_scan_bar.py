"""Folder scan bar: PathSelectField + Scan button for Organizer page."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout

from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.components.molecules import PathSelectField
from anivault.interfaces.gui import theme


class FolderScanBar(QFrame):
    """PathSelectField + Scan button. Emits scan_clicked(path)."""

    scan_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        self._path_field = PathSelectField(placeholder="스캔할 폴더 경로 (또는 폴더 선택 버튼)")
        layout.addWidget(self._path_field, 1)
        scan_btn = Button("스캔", "primary")
        scan_btn.clicked.connect(self._on_scan)
        layout.addWidget(scan_btn)
        self.setStyleSheet(theme.card_panel())

    def _on_scan(self) -> None:
        path = self._path_field.path()
        self.scan_clicked.emit(path)
