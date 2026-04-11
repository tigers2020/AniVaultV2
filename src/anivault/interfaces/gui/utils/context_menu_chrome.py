"""Themed QMenu chrome: QSS plus drop shadow (QSS cannot do box-shadow)."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QMenu

from anivault.interfaces.gui import theme


def apply_context_menu_chrome(menu: QMenu) -> None:
    """Apply popup menu stylesheet and a soft drop shadow."""

    menu.setStyleSheet(theme.view_toggle_menu())
    shadow = QGraphicsDropShadowEffect(menu)
    shadow.setBlurRadius(20)
    shadow.setOffset(0, 6)
    shadow.setColor(QColor(0, 0, 0, 72))
    menu.setGraphicsEffect(shadow)
