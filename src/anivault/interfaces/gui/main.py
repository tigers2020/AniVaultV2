"""GUI entry point. Runs QApplication and MainWindow."""

import sys

from PySide6.QtWidgets import QApplication, QWidget

from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.themes import load_saved_theme, on_theme_changed


def _clear_widget_stylesheets(widget: QWidget) -> None:
    """Clear stylesheet from widget and all descendants so they inherit from app."""
    widget.setStyleSheet("")
    for child in widget.findChildren(QWidget):
        _clear_widget_stylesheets(child)


def run() -> None:
    """Start the GUI application."""
    load_saved_theme()
    app = QApplication(sys.argv)
    window = MainWindow()

    def reapply_stylesheet() -> None:
        app.setStyleSheet(global_stylesheet())
        for w in app.topLevelWidgets():
            if isinstance(w, MainWindow):
                _clear_widget_stylesheets(w)
                break

    on_theme_changed(reapply_stylesheet)
    app.setStyleSheet(global_stylesheet())
    window.show()
    sys.exit(app.exec())
