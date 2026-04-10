"""Main window setup and page switching."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import QMainWindow

from anivault.constants.gui.copy import APP_WINDOW_TITLE, PAGE_META
from anivault.constants.gui.navigation import TAB_ORGANIZER, TAB_SETTINGS, TAB_SUBTITLES
from anivault.constants.gui.theme import (
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
    MAIN_WINDOW_RESIZE_DEBOUNCE_MS,
)
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.templates import MainShell
from anivault.interfaces.gui.themes import set_responsive_density_for_size


class MainWindow(QMainWindow):
    """Top-level Qt window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_WINDOW_TITLE)
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self.resize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self._shell = MainShell()
        self.setCentralWidget(self._shell)
        from anivault.bootstrap.container import AniVaultAppContainer
        from anivault.interfaces.gui.models import PipelineTableModel

        self._app_container = AniVaultAppContainer()
        self._progress_dialog = ProgressDialog(parent=self)
        self._pipeline_model = PipelineTableModel()
        self._pipeline_model_subtitles = PipelineTableModel()
        self._startup_progress_reset_done = False
        self._shell.add_page(
            self._app_container.create_organizer_page(
                pipeline_model=self._pipeline_model,
                progress_dialog=self._progress_dialog,
            )
        )
        self._shell.add_page(
            self._app_container.create_subtitle_organizer_page(
                pipeline_model=self._pipeline_model_subtitles,
                progress_dialog=self._progress_dialog,
            )
        )
        self._shell.add_page(self._app_container.create_settings_page())
        self._shell.tab_clicked.connect(self._on_tab_clicked)
        self._tab_to_index = {
            TAB_ORGANIZER: 0,
            TAB_SUBTITLES: 1,
            TAB_SETTINGS: 2,
        }

        self._responsive_timer = QTimer(self)
        self._responsive_timer.setSingleShot(True)
        self._responsive_timer.timeout.connect(self._apply_responsive_density)
        self._apply_responsive_density()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._startup_progress_reset_done:
            self._startup_progress_reset_done = True
            self._progress_dialog.hide_progress()

    def _on_tab_clicked(self, tab_id: str) -> None:
        title, desc = PAGE_META.get(tab_id, ("", ""))
        self._shell.set_topbar_page(title, desc)
        idx = self._tab_to_index.get(tab_id, 0)
        self._shell.set_current_page(idx)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._responsive_timer.start(MAIN_WINDOW_RESIZE_DEBOUNCE_MS)

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self._app_container.close()
        finally:
            super().closeEvent(event)

    def _apply_responsive_density(self) -> None:
        size = self.size()
        set_responsive_density_for_size(width=size.width(), height=size.height())
