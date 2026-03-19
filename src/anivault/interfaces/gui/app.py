"""MainWindow: assembles MainShell, wires tab switch and page meta."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow

from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.components.organisms import LogList
from anivault.interfaces.gui.templates import MainShell
from anivault.interfaces.gui.themes import set_responsive_density_for_size

PAGE_META = {
    "organizer": (
        "Organizer",
        "폴더 스캔부터 한글 제목 그룹 확정과 최종 경로 미리보기까지 한 화면에서 처리",
    ),
    "operations": (
        "Operations",
        "폴더 구조, 실행, 최근 활동을 한 탭에서 관리",
    ),
    "settings": (
        "Settings",
        "scan/build controls와 path, parse, TMDB 규칙 설정",
    ),
}


class MainWindow(QMainWindow):
    """Main window: shell + stacked pages, tab switch updates topbar and stack."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AniVault V2")
        self.setMinimumSize(1280, 768)
        self.resize(1280, 768)
        self._shell = MainShell()
        self.setCentralWidget(self._shell)
        from anivault.interfaces.gui.composition import (
            create_operations_page,
            create_organizer_page,
            create_settings_page,
        )

        self._progress_dialog = ProgressDialog(parent=self)
        self._shell.add_page(create_organizer_page(progress_dialog=self._progress_dialog))
        self._shell.add_page(create_operations_page())
        self._shell.add_page(create_settings_page())
        self._shell.tab_clicked.connect(self._on_tab_clicked)
        organizer_idx = 0
        operations_idx = 1
        settings_idx = 2
        self._tab_to_index = {
            "organizer": organizer_idx,
            "operations": operations_idx,
            "settings": settings_idx,
        }
        self._log_list: LogList | None = None
        self._find_log_list()
        self._shell.topbar().simulate_clicked.connect(self._on_simulate_clicked)

        self._responsive_timer = QTimer(self)
        self._responsive_timer.setSingleShot(True)
        self._responsive_timer.timeout.connect(self._apply_responsive_density)
        self._apply_responsive_density()

    def _find_log_list(self) -> None:
        stack = self._shell._stack
        for i in range(stack.count()):
            w = stack.widget(i)
            children = w.findChildren(LogList)
            if children:
                self._log_list = children[0]
                return

    def _on_tab_clicked(self, tab_id: str) -> None:
        title, desc = PAGE_META.get(tab_id, ("", ""))
        self._shell.set_topbar_page(title, desc)
        idx = self._tab_to_index.get(tab_id, 0)
        self._shell.set_current_page(idx)

    def _on_simulate_clicked(self) -> None:
        from datetime import datetime

        now = datetime.now()
        time_str = now.strftime("[%H:%M:%S]")
        msg = "Simulated pipeline advanced through parse and TMDB grouping"
        if self._log_list is None:
            self._find_log_list()
        if self._log_list is not None:
            self._log_list.append_entry(time_str, msg)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Debounce: density computation triggers QSS re-apply (expensive).
        self._responsive_timer.start(300)

    def _apply_responsive_density(self) -> None:
        size = self.size()
        set_responsive_density_for_size(width=size.width(), height=size.height())
