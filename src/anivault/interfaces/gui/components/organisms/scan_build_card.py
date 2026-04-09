"""Settings card for source-path configuration."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from anivault.constants.gui.components import (
    SCAN_BUILD_CARD_HEADER_DESCRIPTION,
    SCAN_BUILD_CARD_HEADER_PILL_TEXT,
    SCAN_BUILD_CARD_HEADER_TITLE,
    SCAN_BUILD_CARD_SOURCE_PLACEHOLDER,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, PathSelectField


class ScanBuildCard(QFrame):
    """Source-path settings card."""

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
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        row = QHBoxLayout()
        row.setSpacing(theme.settings_row_gap_px())
        self._source = PathSelectField(placeholder=SCAN_BUILD_CARD_SOURCE_PLACEHOLDER)
        row.addWidget(self._source, 1)
        body.addLayout(row)
        self._source.path_changed.connect(lambda: self.settings_changed.emit())
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def get_values(self) -> dict[str, str]:
        return {"source_path": self._source.path()}

    def set_values(self, data: dict[str, str]) -> None:
        self.blockSignals(True)
        try:
            if "source_path" in data:
                self._source.set_path(data["source_path"])
        finally:
            self.blockSignals(False)
