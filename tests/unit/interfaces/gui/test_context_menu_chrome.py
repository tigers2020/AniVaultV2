from __future__ import annotations

from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMenu

from anivault.interfaces.gui.utils.context_menu_chrome import apply_context_menu_chrome


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_apply_context_menu_chrome_sets_stylesheet_and_shadow() -> None:
    _ensure_app()
    menu = QMenu()
    apply_context_menu_chrome(menu)
    assert isinstance(menu.styleSheet(), str)
    assert len(menu.styleSheet()) > 20
    effect = menu.graphicsEffect()
    assert isinstance(effect, QGraphicsDropShadowEffect)
