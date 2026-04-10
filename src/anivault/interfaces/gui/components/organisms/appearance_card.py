"""appearance_card.py

테마·언어 선택·외형 옵션 카드.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import ComboBox, Label
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n.keys import (
    SETTINGS_APPEARANCE_HEADER_PILL,
    SETTINGS_APPEARANCE_HEADER_SUBTITLE,
    SETTINGS_APPEARANCE_HEADER_TITLE,
    SETTINGS_APPEARANCE_LANGUAGE_LABEL,
    SETTINGS_APPEARANCE_THEME_DARK,
    SETTINGS_APPEARANCE_THEME_LABEL,
    SETTINGS_APPEARANCE_THEME_LIGHT,
    SETTINGS_LANG_OPTION_EN,
    SETTINGS_LANG_OPTION_KO,
)
from anivault.interfaces.gui.themes import get_current_theme_name, list_themes


class AppearanceCard(QFrame):
    """테마·언어 콤보. theme_changed / language_changed 시그널."""

    theme_changed = Signal(str)
    language_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._header = PanelHeader(
            translate(SETTINGS_APPEARANCE_HEADER_TITLE),
            translate(SETTINGS_APPEARANCE_HEADER_SUBTITLE),
            pill_text=translate(SETTINGS_APPEARANCE_HEADER_PILL),
            pill_color="blue",
        )
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._theme_label = Label("", "muted")
        body.addWidget(self._theme_label)
        self._theme_combo = ComboBox(self)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        body.addWidget(self._theme_combo)
        self._language_label = Label("", "muted")
        body.addWidget(self._language_label)
        self._language_combo = ComboBox(self)
        self._language_combo.currentIndexChanged.connect(self._on_language_selected)
        body.addWidget(self._language_combo)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
        self._populate_theme_combo()
        self._populate_language_combo()
        self.retranslate_ui()
        get_i18n_service().language_changed.connect(self._on_app_language_changed)

    def _populate_theme_combo(self) -> None:
        self._theme_combo.blockSignals(True)
        self._theme_combo.clear()
        theme_names = list_themes()
        for name in theme_names:
            if name == "dark":
                label = translate(SETTINGS_APPEARANCE_THEME_DARK)
            elif name == "light":
                label = translate(SETTINGS_APPEARANCE_THEME_LIGHT)
            else:
                label = name.title()
            self._theme_combo.addItem(label, name)
        current = get_current_theme_name()
        idx = self._theme_combo.findData(current)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.blockSignals(False)

    def _populate_language_combo(self) -> None:
        self._language_combo.blockSignals(True)
        self._language_combo.clear()
        for code, key in (("ko", SETTINGS_LANG_OPTION_KO), ("en", SETTINGS_LANG_OPTION_EN)):
            self._language_combo.addItem(translate(key), code)
        current = get_i18n_service().get_current_language()
        idx = self._language_combo.findData(current)
        if idx >= 0:
            self._language_combo.setCurrentIndex(idx)
        self._language_combo.blockSignals(False)

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(SETTINGS_APPEARANCE_HEADER_TITLE),
            translate(SETTINGS_APPEARANCE_HEADER_SUBTITLE),
            translate(SETTINGS_APPEARANCE_HEADER_PILL),
        )
        self._theme_label.setText(translate(SETTINGS_APPEARANCE_THEME_LABEL))
        self._language_label.setText(translate(SETTINGS_APPEARANCE_LANGUAGE_LABEL))
        self._populate_theme_combo()
        self._populate_language_combo()

    def _on_app_language_changed(self, _lang: str) -> None:
        self.retranslate_ui()

    def _on_theme_selected(self, _idx: int | None = None) -> None:
        idx = self._theme_combo.currentIndex()
        if idx >= 0:
            theme_id = self._theme_combo.itemData(idx)
            if theme_id:
                self.theme_changed.emit(str(theme_id))

    def _on_language_selected(self, _idx: int | None = None) -> None:
        idx = self._language_combo.currentIndex()
        if idx >= 0:
            lang = self._language_combo.itemData(idx)
            if lang:
                self.language_changed.emit(str(lang))
