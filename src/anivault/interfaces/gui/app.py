"""app.py

MainWindow: MainShell 조립, 탭 전환·페이지 메타·반응형 밀도.

Author: Pom Kim
"""

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
    """셸 + 스택 페이지. 탭에 따라 탑바·스택 갱신."""

    def __init__(self, parent=None):
        """MainShell·페이지·타이머·로그 리스트 참조를 설정한다.

        Args:
            self: 이 창.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
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
        from anivault.interfaces.gui.models import PipelineTableModel
        from anivault.interfaces.gui.state import GuiState

        self._progress_dialog = ProgressDialog(parent=self)
        self._gui_state = GuiState()
        self._pipeline_model = PipelineTableModel()
        self._shell.add_page(
            create_organizer_page(
                pipeline_model=self._pipeline_model,
                progress_dialog=self._progress_dialog,
            )
        )
        self._shell.add_page(
            create_operations_page(
                pipeline_model=self._pipeline_model,
                progress_dialog=self._progress_dialog,
                gui_state=self._gui_state,
            )
        )
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
        """스택 위젯에서 첫 LogList를 찾아 캐시한다.

        Args:
            self: 이 창.

        Returns:
            None.
        """
        stack = self._shell._stack
        for i in range(stack.count()):
            w = stack.widget(i)
            children = w.findChildren(LogList)
            if children:
                self._log_list = children[0]
                return

    def _on_tab_clicked(self, tab_id: str) -> None:
        """탭 ID에 맞춰 탑바 문구와 스택 인덱스를 바꾼다.

        Args:
            self: 이 창.
            tab_id: organizer | operations | settings.

        Returns:
            None.
        """
        title, desc = PAGE_META.get(tab_id, ("", ""))
        self._shell.set_topbar_page(title, desc)
        idx = self._tab_to_index.get(tab_id, 0)
        self._shell.set_current_page(idx)

    def _on_simulate_clicked(self) -> None:
        """시뮬레이션 로그 한 줄을 Recent Activity에 추가한다.

        Args:
            self: 이 창.

        Returns:
            None.
        """
        from datetime import datetime

        now = datetime.now()
        time_str = now.strftime("[%H:%M:%S]")
        msg = "Simulated pipeline advanced through parse and TMDB grouping"
        if self._log_list is None:
            self._find_log_list()
        if self._log_list is not None:
            self._log_list.append_entry(time_str, msg)

    def resizeEvent(self, event) -> None:
        """리사이즈 디바운스 후 밀도 키를 갱신한다.

        Args:
            self: 이 창.
            event: Qt 리사이즈 이벤트.

        Returns:
            None.
        """
        super().resizeEvent(event)
        # Debounce: density computation triggers QSS re-apply (expensive).
        self._responsive_timer.start(300)

    def _apply_responsive_density(self) -> None:
        """현재 창 크기로 set_responsive_density_for_size를 호출한다.

        Args:
            self: 이 창.

        Returns:
            None.
        """
        size = self.size()
        set_responsive_density_for_size(width=size.width(), height=size.height())
