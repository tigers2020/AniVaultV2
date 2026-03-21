"""folder_scan_bar.py

Organizer용 경로 선택 필드와 스캔·TMDB 매칭 버튼이 있는 상단 바.

Author: Pom Kim
"""

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QSizePolicy

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button
from anivault.interfaces.gui.components.molecules import PathSelectField


class FolderScanBar(QFrame):
    """경로 필드·스캔·매칭 버튼. scan_clicked(path)·path_changed(path) 등을 emit한다."""

    scan_clicked = Signal(str)
    match_clicked = Signal()
    path_changed = Signal(str)

    def __init__(self, parent=None):
        """레이아웃·버튼·시그널 연결과 고정 높이 동기화를 초기화한다.

        Args:
            self: 이 바 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
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
        """설정에서 복원한 경로를 PathSelectField에 반영한다.

        Args:
            self: 이 바 인스턴스.
            path: 표시할 폴더 경로.

        Returns:
            None.
        """
        self._path_field.set_path(path)

    def _on_scan(self) -> None:
        """현재 필드 경로로 scan_clicked 시그널을 emit한다.

        Args:
            self: 이 바 인스턴스.

        Returns:
            None.
        """
        path = self._path_field.path()
        self.scan_clicked.emit(path)

    def _sync_fixed_height(self) -> None:
        """현재 폰트·스타일에 맞춰 카드 고정 높이를 layout sizeHint로 맞춘다.

        Args:
            self: 이 바 인스턴스.

        Returns:
            None.
        """
        h = int(self.layout().sizeHint().height()) if self.layout() is not None else 0
        if h <= 0:
            h = int(self.sizeHint().height())
        if h > 0:
            self.setFixedHeight(h)

    def changeEvent(self, event: QEvent) -> None:
        """폰트·스타일 변경 시 바 높이를 재동기화한다.

        Args:
            self: 이 바 인스턴스.
            event: Qt 변경 이벤트.

        Returns:
            None.
        """
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_fixed_height()
