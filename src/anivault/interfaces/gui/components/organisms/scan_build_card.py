"""Settings card for source-path configuration."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, PathSelectField
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


class ScanBuildCard(QFrame):
    """Source-path settings card."""

    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._header = PanelHeader(
            translate(K.SETTINGS_SCAN_BUILD_TITLE),
            translate(K.SETTINGS_SCAN_BUILD_DESC),
            pill_text=translate(K.SETTINGS_SCAN_BUILD_PILL),
            pill_color="blue",
        )
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        row = QHBoxLayout()
        row.setSpacing(theme.settings_row_gap_px())
        self._source = PathSelectField(
            parent=self,
            placeholder_key=K.SETTINGS_SCAN_BUILD_SOURCE_PH,
        )
        row.addWidget(self._source, 1)
        body.addLayout(row)
        self._source.path_changed.connect(lambda *_args: self.settings_changed.emit())
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(K.SETTINGS_SCAN_BUILD_TITLE),
            translate(K.SETTINGS_SCAN_BUILD_DESC),
            pill_text=translate(K.SETTINGS_SCAN_BUILD_PILL),
        )
        self._source.retranslate_ui()

    def get_values(self) -> dict[str, str]:
        return {"source_path": self._source.path()}

    def set_values(self, data: dict[str, str]) -> None:
        self.blockSignals(True)
        try:
            if "source_path" in data:
                self._source.set_path(data["source_path"])
        finally:
            self.blockSignals(False)
