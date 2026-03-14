"""GUI entry point. Runs QApplication and MainWindow."""

import sys

from PySide6.QtWidgets import QApplication

from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.app import MainWindow


def run() -> None:
    """Start the GUI application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(global_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
