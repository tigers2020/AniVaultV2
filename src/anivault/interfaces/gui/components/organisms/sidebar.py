"""Sidebar: brand + main navigation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import Brand, NavItem
from anivault.interfaces.gui.themes import on_density_changed


class Sidebar(QWidget):
    """Left sidebar: brand and main nav only."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._apply_responsive_metrics()
        self.setStyleSheet(theme.sidebar())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(0)
        layout.addWidget(Brand())
        nav_title = QLabel("Main Views")
        nav_title.setStyleSheet(theme.sidebar_nav_title())
        layout.addWidget(nav_title)
        self._organizer_btn = NavItem("Organizer", "organizer")
        self._organizer_btn.setChecked(True)
        self._operations_btn = NavItem("Operations", "operations")
        self._settings_btn = NavItem("Settings", "settings")
        nav_buttons = QWidget()
        nav_buttons_layout = QVBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(8)
        for btn in (self._organizer_btn, self._operations_btn, self._settings_btn):
            btn.tab_clicked.connect(self.tab_clicked.emit)
            nav_buttons_layout.addWidget(btn)
        layout.addWidget(nav_buttons)
        layout.addStretch()

        on_density_changed(self._apply_responsive_metrics)

    def set_active_tab(self, tab_id: str) -> None:
        self._organizer_btn.setChecked(tab_id == "organizer")
        self._operations_btn.setChecked(tab_id == "operations")
        self._settings_btn.setChecked(tab_id == "settings")

    def _apply_responsive_metrics(self) -> None:
        self.setFixedWidth(theme.sidebar_width_px())
