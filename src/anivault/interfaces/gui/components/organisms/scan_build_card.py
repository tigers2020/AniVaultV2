"""scan_build_card.py

스캔 입력과 단계 버튼 카드.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from anivault.constants.gui.components import (
    SCAN_BUILD_CARD_BUTTON_BUILD_PLAN,
    SCAN_BUILD_CARD_BUTTON_PARSE,
    SCAN_BUILD_CARD_BUTTON_QUERY_TMDB,
    SCAN_BUILD_CARD_BUTTON_SCAN,
    SCAN_BUILD_CARD_HEADER_DESCRIPTION,
    SCAN_BUILD_CARD_HEADER_PILL_TEXT,
    SCAN_BUILD_CARD_HEADER_TITLE,
    SCAN_BUILD_CARD_SOURCE_PLACEHOLDER,
    SCAN_BUILD_CARD_TMDB_MODES,
    SCAN_BUILD_CARD_UNKNOWN_MODES,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, ComboBox
from anivault.interfaces.gui.components.molecules import PanelHeader, PathSelectField


class ScanBuildCard(QFrame):
    """파이프라인 입력과 버튼 모음 카드."""

    scan_clicked = Signal(str)
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                SCAN_BUILD_CARD_HEADER_TITLE,
                SCAN_BUILD_CARD_HEADER_DESCRIPTION,
                pill_text=SCAN_BUILD_CARD_HEADER_PILL_TEXT,
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        row1 = QHBoxLayout()
        row1.setSpacing(10)
        self._source = PathSelectField(placeholder=SCAN_BUILD_CARD_SOURCE_PLACEHOLDER)
        row1.addWidget(self._source, 1)
        body.addLayout(row1)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self._tmdb_mode = ComboBox()
        self._tmdb_mode.addItems(SCAN_BUILD_CARD_TMDB_MODES)
        row2.addWidget(self._tmdb_mode)
        self._unknown_mode = ComboBox()
        self._unknown_mode.addItems(SCAN_BUILD_CARD_UNKNOWN_MODES)
        row2.addWidget(self._unknown_mode)
        row2.addStretch()
        body.addLayout(row2)
        self._source.path_changed.connect(lambda: self.settings_changed.emit())
        self._tmdb_mode.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        self._unknown_mode.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        scan_btn = Button(SCAN_BUILD_CARD_BUTTON_SCAN, "primary")
        scan_btn.clicked.connect(self._on_scan)
        action_row.addWidget(scan_btn)
        action_row.addWidget(Button(SCAN_BUILD_CARD_BUTTON_PARSE))
        action_row.addWidget(Button(SCAN_BUILD_CARD_BUTTON_QUERY_TMDB))
        action_row.addWidget(Button(SCAN_BUILD_CARD_BUTTON_BUILD_PLAN, "warn"))
        body.addLayout(action_row)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def _on_scan(self) -> None:
        self.scan_clicked.emit(self._source.path())

    def get_values(self) -> dict[str, str]:
        return {
            "source_path": self._source.path(),
            "tmdb_mode": self._tmdb_mode.currentText(),
            "unknown_mode": self._unknown_mode.currentText(),
        }

    def set_values(self, data: dict[str, str]) -> None:
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
