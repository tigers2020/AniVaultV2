"""scan_build_card.py

소스 입력 + TMDB/Unknown 콤보 + 스캔·빌드 버튼 줄.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, ComboBox
from anivault.interfaces.gui.components.molecules import PanelHeader, PathSelectField


class ScanBuildCard(QFrame):
    """파이프라인 입력·버튼만 모음. 로직은 Presenter/Worker."""

    scan_clicked = Signal(str)
    settings_changed = Signal()

    def __init__(self, parent=None):
        """필드·시그널·버튼을 배치한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Scan and Build Plan",
                "입력 폴더 스캔·파이프라인 단계는 여기서; 출력 루트(Target root)는 아래 Path Rules에서 설정",
                pill_text="Pipeline Controls",
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self._source = PathSelectField(placeholder="Source: G:/Animations; D:/Incoming_Downloads")
        row1.addWidget(self._source, 1)
        body.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self._tmdb_mode = ComboBox()
        self._tmdb_mode.addItems(["TMDB TV Search", "TMDB Multi Search"])
        row2.addWidget(self._tmdb_mode)
        self._unknown_mode = ComboBox()
        self._unknown_mode.addItems(["Unknown to Needs_Review", "Leave unknown in source"])
        row2.addWidget(self._unknown_mode)
        row2.addStretch()
        body.addLayout(row2)
        self._source.path_changed.connect(lambda: self.settings_changed.emit())
        self._tmdb_mode.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        self._unknown_mode.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        scan_btn = Button("1. Scan Folder", "primary")
        scan_btn.clicked.connect(self._on_scan)
        action_row.addWidget(scan_btn)
        action_row.addWidget(Button("2. Parse Names"))
        action_row.addWidget(Button("3. Query TMDB"))
        action_row.addWidget(Button("4. Build Move Plan", "warn"))
        body.addLayout(action_row)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def _on_scan(self) -> None:
        """소스 경로로 scan_clicked를보낸다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        path = self._source.path()
        self.scan_clicked.emit(path)

    def get_values(self) -> dict[str, str]:
        """현재 폼 값을 dict로 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            source_path, tmdb_mode, unknown_mode.
        """
        return {
            "source_path": self._source.path(),
            "tmdb_mode": self._tmdb_mode.currentText(),
            "unknown_mode": self._unknown_mode.currentText(),
        }

    def set_values(self, data: dict[str, str]) -> None:
        """dict 값으로 필드를 채운다(시그널 일시 차단).

        Args:
            self: 이 위젯.
            data: 키별 문자열.

        Returns:
            None.
        """
        self.blockSignals(True)
        try:
            if "source_path" in data:
                self._source.set_path(data["source_path"])
            if "tmdb_mode" in data:
                idx = self._tmdb_mode.findText(data["tmdb_mode"])
                if idx >= 0:
                    self._tmdb_mode.setCurrentIndex(idx)
            if "unknown_mode" in data:
                idx = self._unknown_mode.findText(data["unknown_mode"])
                if idx >= 0:
                    self._unknown_mode.setCurrentIndex(idx)
        finally:
            self.blockSignals(False)
