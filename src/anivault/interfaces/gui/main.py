"""GUI entry point. Runs QApplication and MainWindow."""

import sys

from PySide6.QtWidgets import QApplication, QLayout, QWidget

from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.themes import load_saved_theme, on_density_changed, on_theme_changed


def _clear_widget_stylesheets(widget: QWidget) -> None:
    """Clear stylesheet from widget and all descendants so they inherit from app."""
    widget.setStyleSheet("")
    for child in widget.findChildren(QWidget):
        _clear_widget_stylesheets(child)


def _enforce_min_layout_padding_and_margin(widget: QWidget, minimum_px: int = 5) -> None:
    """Apply minimum layout/widget margins so UI keeps base breathing room."""

    def _clamp_layout(layout: QLayout) -> None:
        margins = layout.contentsMargins()
        layout.setContentsMargins(
            max(minimum_px, margins.left()),
            max(minimum_px, margins.top()),
            max(minimum_px, margins.right()),
            max(minimum_px, margins.bottom()),
        )
        if layout.spacing() < minimum_px:
            layout.setSpacing(minimum_px)

    margins = widget.contentsMargins()
    widget.setContentsMargins(
        max(minimum_px, margins.left()),
        max(minimum_px, margins.top()),
        max(minimum_px, margins.right()),
        max(minimum_px, margins.bottom()),
    )
    layout = widget.layout()
    if layout is not None:
        _clamp_layout(layout)
    for child in widget.findChildren(QWidget):
        child_margins = child.contentsMargins()
        child.setContentsMargins(
            max(minimum_px, child_margins.left()),
            max(minimum_px, child_margins.top()),
            max(minimum_px, child_margins.right()),
            max(minimum_px, child_margins.bottom()),
        )
        child_layout = child.layout()
        if child_layout is not None:
            _clamp_layout(child_layout)


def run() -> None:
    """Start the GUI application."""
    load_saved_theme()
    app = QApplication(sys.argv)
    window = MainWindow()

    def reapply_stylesheet_after_color_change() -> None:
        # Full re-apply for light/dark changes (colors/gradients may be
        # embedded in per-widget QSS strings).
        app.setStyleSheet(global_stylesheet())
        for w in app.topLevelWidgets():
            if isinstance(w, MainWindow):
                _clear_widget_stylesheets(w)
                break

    def reapply_stylesheet_after_density_change() -> None:
        # Density changes only affect root font-size / scaled radii.
        # Avoid clearing widget-level stylesheets during resize to prevent
        # expensive recursive style mutations (which can freeze the UI).
        app.setStyleSheet(global_stylesheet())

    on_theme_changed(reapply_stylesheet_after_color_change)
    on_density_changed(reapply_stylesheet_after_density_change)
    app.setStyleSheet(global_stylesheet())
    _clear_widget_stylesheets(window)
    _enforce_min_layout_padding_and_margin(window, minimum_px=5)
    window.show()
    sys.exit(app.exec())
