"""main_shell.py

Sidebar + Topbar + QStackedWidget 페이지 영역.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import Sidebar, Topbar


class MainShell(QWidget):
    """고정 너비 사이드바와 메인(탑바+스택)."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        """사이드바·탑바·스택을 가로로 배치한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._sidebar = Sidebar()
        self._sidebar.tab_clicked.connect(self._on_tab_clicked)
        layout.addWidget(self._sidebar)
        main = QFrame()
        main_layout = QVBoxLayout(main)
        pad = theme.layout_main_padding()
        main_layout.setContentsMargins(pad, pad, pad, pad)
        main_layout.setSpacing(theme.page_section_gap_px())
        self._topbar = Topbar()
        main_layout.addWidget(self._topbar)
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)
        layout.addWidget(main, 1)

    def _on_tab_clicked(self, tab_id: str) -> None:
        """사이드바 활성 탭을 맞추고 tab_clicked를보낸다.

        Args:
            self: 이 위젯.
            tab_id: 탭 식별자.

        Returns:
            None.
        """
        self._sidebar.set_active_tab(tab_id)
        self.tab_clicked.emit(tab_id)

    def set_topbar_page(self, title: str, description: str) -> None:
        """탑바 제목·설명을 바꾼다.

        Args:
            self: 이 위젯.
            title: 페이지 제목.
            description: 부제.

        Returns:
            None.
        """
        self._topbar.set_page(title, description)

    def add_page(self, widget: QWidget) -> None:
        """스택에 페이지 위젯을 추가한다.

        Args:
            self: 이 위젯.
            widget: 페이지 루트.

        Returns:
            None.
        """
        self._stack.addWidget(widget)

    def set_current_page(self, index: int) -> None:
        """스택 현재 인덱스를 설정한다.

        Args:
            self: 이 위젯.
            index: QStackedWidget 인덱스.

        Returns:
            None.
        """
        self._stack.setCurrentIndex(index)

    def topbar(self) -> Topbar:
        """탑바 위젯을 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            Topbar.
        """
        return self._topbar

    def sidebar(self) -> Sidebar:
        """사이드바 위젯을 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            Sidebar.
        """
        return self._sidebar

    def retranslate_ui(self) -> None:
        """Refresh translated strings on shell chrome."""
        self._sidebar.retranslate_ui()
