"""folder_scan_bar.py

Organizer 상단의 경로 선택과 스캔/매칭 바.

Author: Pom Kim
"""

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QSizePolicy

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.components.molecules import PathSelectField
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


class FolderScanBar(QFrame):
    """경로 입력과 스캔, 매칭 버튼."""

    scan_clicked = Signal(str)
    match_clicked = Signal()
    dry_run_clicked = Signal()
    path_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        body_padding = theme.card_body_padding_px()
        layout.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        layout.setHorizontalSpacing(theme.inline_control_gap_px())
        layout.setVerticalSpacing(theme.compact_gap_px())
        layout.setColumnStretch(0, 1)
        self._path_field = PathSelectField(
            parent=self,
            placeholder_key=K.ORG_SCANBAR_PATH_PLACEHOLDER,
        )
        self._path_field.path_changed.connect(lambda path: self.path_changed.emit(path))
        layout.addWidget(self._path_field, 0, 0, 1, 3)
        self._scan_btn = Button(translate(K.ORG_SCANBAR_BTN_SCAN), "primary")
        self._scan_btn.clicked.connect(self._on_scan)
        layout.addWidget(self._scan_btn, 1, 0)
        self._match_btn = Button(translate(K.ORG_SCANBAR_BTN_MATCH))
        self._match_btn.clicked.connect(self.match_clicked.emit)
        layout.addWidget(self._match_btn, 1, 1)
        self._dry_run_btn = Button(translate(K.ORG_SCANBAR_BTN_DRY_RUN))
        self._dry_run_btn.setEnabled(False)
        self._dry_run_btn.clicked.connect(self.dry_run_clicked.emit)
        layout.addWidget(self._dry_run_btn, 1, 2)
        self.setStyleSheet(theme.card_panel())
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed))
        self._sync_fixed_height()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._path_field.retranslate_ui()
        self._scan_btn.setText(translate(K.ORG_SCANBAR_BTN_SCAN))
        self._match_btn.setText(translate(K.ORG_SCANBAR_BTN_MATCH))
        self._dry_run_btn.setText(translate(K.ORG_SCANBAR_BTN_DRY_RUN))

    def set_dry_run_enabled(self, enabled: bool) -> None:
        self._dry_run_btn.setEnabled(enabled)

    def set_pipeline_busy(self, busy: bool) -> None:
        """백그라운드 파이프라인 작업 중이면 스캔·매칭 버튼을 비활성화한다."""

        self._scan_btn.setEnabled(not busy)
        self._match_btn.setEnabled(not busy)

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
