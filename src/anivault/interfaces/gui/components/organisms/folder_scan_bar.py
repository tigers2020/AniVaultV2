"""folder_scan_bar.py

Organizer 상단의 경로 선택과 스캔/매칭 바.

Author: Pom Kim
"""

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

from anivault.constants.gui.components import (
    FOLDER_SCAN_BAR_BUTTON_DRY_RUN,
    FOLDER_SCAN_BAR_BUTTON_MATCH,
    FOLDER_SCAN_BAR_BUTTON_SCAN,
    FOLDER_SCAN_BAR_PATH_PLACEHOLDER,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.components.molecules import PathSelectField


class FolderScanBar(QFrame):
    """경로 입력과 스캔, 매칭 버튼."""

    scan_clicked = Signal(str)
    match_clicked = Signal()
    dry_run_clicked = Signal()
    path_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)
        self._path_field = PathSelectField(placeholder=FOLDER_SCAN_BAR_PATH_PLACEHOLDER)
        self._path_field.path_changed.connect(self.path_changed.emit)
        layout.addWidget(self._path_field, 1)
        scan_btn = Button(FOLDER_SCAN_BAR_BUTTON_SCAN, "primary")
        scan_btn.clicked.connect(self._on_scan)
        layout.addWidget(scan_btn)
        match_btn = Button(FOLDER_SCAN_BAR_BUTTON_MATCH)
        match_btn.clicked.connect(self.match_clicked.emit)
        layout.addWidget(match_btn)
        self._dry_run_btn = Button(FOLDER_SCAN_BAR_BUTTON_DRY_RUN)
        self._dry_run_btn.setEnabled(False)
        self._dry_run_btn.clicked.connect(self.dry_run_clicked.emit)
        layout.addWidget(self._dry_run_btn)
        self.setStyleSheet(theme.card_panel())
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed))
        self._sync_fixed_height()

    def set_dry_run_enabled(self, enabled: bool) -> None:
        self._dry_run_btn.setEnabled(enabled)

    def set_path(self, path: str) -> None:
        self._path_field.set_path(path)

    def _on_scan(self) -> None:
        self.scan_clicked.emit(self._path_field.path())

    def _sync_fixed_height(self) -> None:
        layout = self.layout()
        h = int(layout.sizeHint().height()) if layout is not None else 0
        if h <= 0:
            h = int(self.sizeHint().height())
        if h > 0:
            self.setFixedHeight(h)

    def changeEvent(self, arg__1: QEvent) -> None:
        event = arg__1
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_fixed_height()
