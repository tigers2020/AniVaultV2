"""main.py

GUI 진입: QApplication·MainWindow·테마 재적용 조정자.

Author: Pom Kim
"""

import sys

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication, QWidget

from anivault.bootstrap.env_file import load_into_os_environ
from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.theme import global_stylesheet
from anivault.interfaces.gui.themes import load_saved_theme, on_density_changed, on_theme_changed


def _clear_widget_stylesheets(widget: QWidget) -> None:
    """위젯과 자손의 로컬 스타일시트를 비워 앱 전역을 상속받게 한다.

    Args:
        widget: 루트 위젯.

    Returns:
        None.
    """
    widget.setStyleSheet("")
    for child in widget.findChildren(QWidget):
        child.setStyleSheet("")


class _ThemeReapplyCoordinator(QObject):
    """테마 QSS 재적용을 배치·디바운스한다."""

    def __init__(self, *, app: QApplication, window: MainWindow) -> None:
        """타이머와 배치 상태를 초기화한다.

        Args:
            self: 이 조정자.
            app: QApplication.
            window: 메인 창.

        Returns:
            None.
        """
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
        """라이트/다크 전환 후 전체 재적용을 예약한다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
        self._pending_color = True
        if not self._timer.isActive():
            self._timer.start(0)

    def request_density_change(self) -> None:
        """밀도 변경 시 전역 QSS만 갱신하도록 예약한다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
        # Color-theme swap has priority because it includes app stylesheet reset.
        if self._pending_color or self._clear_targets:
            self._pending_density = True
            return
        self._pending_density = True
        if not self._timer.isActive():
            self._timer.start(0)

    def _reapply_global_stylesheet(self) -> None:
        """topLevel 위젯 업데이트를 잠시 끄고 app QSS를 설정한다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
        top_level = self._app.topLevelWidgets()
        for widget in top_level:
            widget.setUpdatesEnabled(False)
        try:
            self._app.setStyleSheet(global_stylesheet())
        finally:
            for widget in top_level:
                widget.setUpdatesEnabled(True)

    def _start_color_batch(self) -> None:
        """전역 적용 후 로컬 스타일이 있는 위젯 목록을 만든다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
        self._reapply_global_stylesheet()
        # Clear only widgets that currently carry a local stylesheet.
        # This avoids a full recursive mutation over every descendant.
        all_widgets = [self._window, *self._window.findChildren(QWidget)]
        self._clear_targets = [w for w in all_widgets if w.styleSheet()]
        self._clear_index = 0

    def _continue_color_batch(self) -> None:
        """다음 배치만큼 위젯 스타일시트를 비운다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
        end = min(self._clear_index + self._batch_size, len(self._clear_targets))
        for idx in range(self._clear_index, end):
            self._clear_targets[idx].setStyleSheet("")
        self._clear_index = end
        if self._clear_index >= len(self._clear_targets):
            self._clear_targets = []
            self._clear_index = 0

    def _process(self) -> None:
        """타이머 틱: 배치 클리어 → 색상 → 밀도 순으로 처리한다.

        Args:
            self: 이 조정자.

        Returns:
            None.
        """
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


def run() -> None:
    """환경·테마·앱·MainWindow를 띄우고 이벤트 루프를 실행한다.

    Args:
        없음.

    Returns:
        None. 프로세스는 app.exec()로 종료한다.
    """
    load_into_os_environ()
    load_saved_theme()
    app = QApplication(sys.argv)
    window = MainWindow()

    coordinator = _ThemeReapplyCoordinator(app=app, window=window)

    def reapply_stylesheet_after_color_change() -> None:
        """테마(색) 변경 콜백: 배치 재적용을 요청한다.

        Args:
            없음.

        Returns:
            None.
        """
        # Full re-apply for light/dark changes, but scheduled in small batches
        # so a theme switch does not block the UI thread for too long.
        coordinator.request_color_change()

    def reapply_stylesheet_after_density_change() -> None:
        """밀도 변경 콜백: 위젯 로컬 클리어 없이 전역만 갱신한다.

        Args:
            없음.

        Returns:
            None.
        """
        # Density changes only affect root font-size / scaled radii.
        # Avoid clearing widget-level stylesheets during resize.
        coordinator.request_density_change()

    on_theme_changed(reapply_stylesheet_after_color_change)
    on_density_changed(reapply_stylesheet_after_density_change)
    app.setStyleSheet(global_stylesheet())
    _clear_widget_stylesheets(window)
    window.show()
    sys.exit(app.exec())
