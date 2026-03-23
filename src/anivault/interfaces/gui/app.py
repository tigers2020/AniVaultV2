"""app.py

MainWindow: MainShell 조립, 탭 전환·페이지 메타·반응형 밀도.

Author: Pom Kim
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow

from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.templates import MainShell
from anivault.interfaces.gui.themes import set_responsive_density_for_size

PAGE_META = {
    "organizer": (
        "Organizer",
        "폴더 스캔부터 한글 제목 그룹 확정과 최종 경로 미리보기까지 한 화면에서 처리",
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
            create_organizer_page,
            create_settings_page,
        )
        from anivault.interfaces.gui.models import PipelineTableModel

        self._progress_dialog = ProgressDialog(parent=self)
        self._pipeline_model = PipelineTableModel()
        self._shell.add_page(
            create_organizer_page(
                pipeline_model=self._pipeline_model,
                progress_dialog=self._progress_dialog,
            )
        )
        self._shell.add_page(create_settings_page())
        self._shell.tab_clicked.connect(self._on_tab_clicked)
        self._tab_to_index = {
            "organizer": 0,
            "settings": 1,
        }

        self._responsive_timer = QTimer(self)
        self._responsive_timer.setSingleShot(True)
        self._responsive_timer.timeout.connect(self._apply_responsive_density)
        self._apply_responsive_density()

    def _on_tab_clicked(self, tab_id: str) -> None:
        """탭 ID에 맞춰 탑바 문구와 스택 인덱스를 바꾼다.

        Args:
            self: 이 창.
            tab_id: organizer | settings.

        Returns:
            None.
        """
        title, desc = PAGE_META.get(tab_id, ("", ""))
        self._shell.set_topbar_page(title, desc)
        idx = self._tab_to_index.get(tab_id, 0)
        self._shell.set_current_page(idx)

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
