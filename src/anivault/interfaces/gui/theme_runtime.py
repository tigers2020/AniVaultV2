"""Runtime helpers for applying the active GUI theme."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from anivault.interfaces.gui.theme import global_stylesheet


def clear_widget_stylesheets(widget: QWidget) -> None:
    """Clear local stylesheets so descendants inherit the app stylesheet."""

    widget.setStyleSheet("")
    for child in widget.findChildren(QWidget):
        child.setStyleSheet("")


class ThemeReapplyCoordinator(QObject):
    """Batch theme reapplication so color swaps do not block the UI thread."""

    def __init__(self, *, app: QApplication, window: QWidget) -> None:
        super().__init__(window)
        self._app = app
        self._window = window
        self._batch_size = 240
        self._pending_density = False
        self._pending_color = False
        self._clear_targets: list[QWidget] = []
        self._clear_index = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._process)

    def request_color_change(self) -> None:
        """Schedule a full light/dark theme reapply."""

        self._pending_color = True
        if not self._timer.isActive():
            self._timer.start(0)

    def request_density_change(self) -> None:
        """Schedule a density-only stylesheet refresh."""

        if self._pending_color or self._clear_targets:
            self._pending_density = True
            return
        self._pending_density = True
        if not self._timer.isActive():
            self._timer.start(0)

    def _reapply_global_stylesheet(self) -> None:
        top_level = self._app.topLevelWidgets()
        for widget in top_level:
            widget.setUpdatesEnabled(False)
        try:
            self._app.setStyleSheet(global_stylesheet())
        finally:
            for widget in top_level:
                widget.setUpdatesEnabled(True)

    def _start_color_batch(self) -> None:
        self._reapply_global_stylesheet()
        all_widgets = [self._window, *self._window.findChildren(QWidget)]
        self._clear_targets = [widget for widget in all_widgets if widget.styleSheet()]
        self._clear_index = 0

    def _continue_color_batch(self) -> None:
        end = min(self._clear_index + self._batch_size, len(self._clear_targets))
        for idx in range(self._clear_index, end):
            self._clear_targets[idx].setStyleSheet("")
        self._clear_index = end
        if self._clear_index >= len(self._clear_targets):
            self._clear_targets = []
            self._clear_index = 0

    def _process(self) -> None:
        if self._clear_targets:
            self._continue_color_batch()
            if self._clear_targets:
                self._timer.start(0)
                return

        if self._pending_color:
            self._pending_color = False
            self._start_color_batch()
            if self._clear_targets:
                self._timer.start(0)
                return

        if self._pending_density:
            self._pending_density = False
            self._reapply_global_stylesheet()
