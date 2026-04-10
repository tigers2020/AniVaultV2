"""Sidebar navigation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from anivault.constants.gui.navigation import TAB_ORGANIZER, TAB_SETTINGS, TAB_SUBTITLES
from anivault.constants.gui.theme import SIDEBAR_NAV_SPACING_PX
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import Brand, NavItem
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n.keys import (
    SHELL_SIDEBAR_TITLE,
    SHELL_TAB_ORGANIZER,
    SHELL_TAB_SETTINGS,
    SHELL_TAB_SUBTITLES,
)
from anivault.interfaces.gui.themes import on_density_changed


class Sidebar(QWidget):
    """Main app sidebar."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._apply_responsive_metrics()
        self.setStyleSheet(theme.sidebar())
        layout = QVBoxLayout(self)
        sidebar_padding = theme.sidebar_padding_px()
        layout.setContentsMargins(
            sidebar_padding,
            sidebar_padding,
            sidebar_padding,
            sidebar_padding,
        )
        layout.setSpacing(0)
        self._brand = Brand()
        layout.addWidget(self._brand)
        self._nav_title = QLabel()
        self._nav_title.setStyleSheet(theme.sidebar_nav_title())
        layout.addWidget(self._nav_title)
        self._organizer_btn = NavItem("", TAB_ORGANIZER)
        self._organizer_btn.setChecked(True)
        self._subtitles_btn = NavItem("", TAB_SUBTITLES)
        self._settings_btn = NavItem("", TAB_SETTINGS)
        nav_buttons = QWidget()
        nav_buttons_layout = QVBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(max(SIDEBAR_NAV_SPACING_PX, theme.compact_gap_px()))
        for btn in (self._organizer_btn, self._subtitles_btn, self._settings_btn):
            btn.tab_clicked.connect(self.tab_clicked.emit)
            nav_buttons_layout.addWidget(btn)
        layout.addWidget(nav_buttons)
        layout.addStretch()
        on_density_changed(self._apply_responsive_metrics)
        self.retranslate_ui()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._brand.retranslate_ui()
        self._nav_title.setText(translate(SHELL_SIDEBAR_TITLE))
        self._organizer_btn.set_label_text(translate(SHELL_TAB_ORGANIZER))
        self._subtitles_btn.set_label_text(translate(SHELL_TAB_SUBTITLES))
        self._settings_btn.set_label_text(translate(SHELL_TAB_SETTINGS))

    def set_active_tab(self, tab_id: str) -> None:
        self._organizer_btn.setChecked(tab_id == TAB_ORGANIZER)
        self._subtitles_btn.setChecked(tab_id == TAB_SUBTITLES)
        self._settings_btn.setChecked(tab_id == TAB_SETTINGS)

    def _apply_responsive_metrics(self) -> None:
        self.setFixedWidth(theme.sidebar_width_px())
