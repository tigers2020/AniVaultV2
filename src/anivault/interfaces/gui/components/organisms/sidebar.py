"""Sidebar navigation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from anivault.constants.gui.copy import SIDEBAR_TAB_LABELS, SIDEBAR_TITLE
from anivault.constants.gui.navigation import TAB_ORGANIZER, TAB_SETTINGS, TAB_SUBTITLES
from anivault.constants.gui.theme import SIDEBAR_NAV_SPACING_PX
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import Brand, NavItem
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
        layout.addWidget(Brand())
        nav_title = QLabel(SIDEBAR_TITLE)
        nav_title.setStyleSheet(theme.sidebar_nav_title())
        layout.addWidget(nav_title)
        self._organizer_btn = NavItem(SIDEBAR_TAB_LABELS[TAB_ORGANIZER], TAB_ORGANIZER)
        self._organizer_btn.setChecked(True)
        self._subtitles_btn = NavItem(SIDEBAR_TAB_LABELS[TAB_SUBTITLES], TAB_SUBTITLES)
        self._settings_btn = NavItem(SIDEBAR_TAB_LABELS[TAB_SETTINGS], TAB_SETTINGS)
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

    def set_active_tab(self, tab_id: str) -> None:
        self._organizer_btn.setChecked(tab_id == TAB_ORGANIZER)
        self._subtitles_btn.setChecked(tab_id == TAB_SUBTITLES)
        self._settings_btn.setChecked(tab_id == TAB_SETTINGS)

    def _apply_responsive_metrics(self) -> None:
        self.setFixedWidth(theme.sidebar_width_px())
