"""GUI entrypoint."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from anivault.bootstrap.env_file import load_into_os_environ
from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.theme_runtime import (
    ThemeReapplyCoordinator as _ThemeReapplyCoordinator,
)
from anivault.interfaces.gui.theme_runtime import (
    clear_widget_stylesheets as _clear_widget_stylesheets,
)
from anivault.interfaces.gui.themes import load_saved_theme, on_density_changed, on_theme_changed


def run() -> None:
    """Start the GUI application and enter the Qt event loop."""

    load_into_os_environ()
    load_saved_theme()
    app = QApplication(sys.argv)
    window = MainWindow()
    coordinator = _ThemeReapplyCoordinator(app=app, window=window)

    def reapply_stylesheet_after_color_change() -> None:
        coordinator.request_color_change()

    def reapply_stylesheet_after_density_change() -> None:
        coordinator.request_density_change()

    on_theme_changed(reapply_stylesheet_after_color_change)
    on_density_changed(reapply_stylesheet_after_density_change)
    app.setStyleSheet(global_stylesheet())
    _clear_widget_stylesheets(window)
    window.show()
    sys.exit(app.exec())
