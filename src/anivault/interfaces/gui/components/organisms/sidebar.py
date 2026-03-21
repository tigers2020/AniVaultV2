"""sidebar.py

브랜드 + 메인 내비게이션 사이드바.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import Brand, NavItem
from anivault.interfaces.gui.themes import on_density_changed


class Sidebar(QWidget):
    """왼쪽: 브랜드와 Organizer/Operations/Settings 탭."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        """내비 버튼과 밀도 변경 콜백을 연결한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._apply_responsive_metrics()
        self.setStyleSheet(theme.sidebar())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(0)
        layout.addWidget(Brand())
        nav_title = QLabel("Main Views")
        nav_title.setStyleSheet(theme.sidebar_nav_title())
        layout.addWidget(nav_title)
        self._organizer_btn = NavItem("Organizer", "organizer")
        self._organizer_btn.setChecked(True)
        self._operations_btn = NavItem("Operations", "operations")
        self._settings_btn = NavItem("Settings", "settings")
        nav_buttons = QWidget()
        nav_buttons_layout = QVBoxLayout(nav_buttons)
        nav_buttons_layout.setContentsMargins(0, 0, 0, 0)
        nav_buttons_layout.setSpacing(8)
        for btn in (self._organizer_btn, self._operations_btn, self._settings_btn):
            btn.tab_clicked.connect(self.tab_clicked.emit)
            nav_buttons_layout.addWidget(btn)
        layout.addWidget(nav_buttons)
        layout.addStretch()

        on_density_changed(self._apply_responsive_metrics)

    def set_active_tab(self, tab_id: str) -> None:
        """tab_id에 맞춰 NavItem 체크 상태를 맞춘다.

        Args:
            self: 이 위젯.
            tab_id: organizer | operations | settings.

        Returns:
            None.
        """
        self._organizer_btn.setChecked(tab_id == "organizer")
        self._operations_btn.setChecked(tab_id == "operations")
        self._settings_btn.setChecked(tab_id == "settings")

    def _apply_responsive_metrics(self) -> None:
        """현재 밀도에 맞는 사이드바 고정 너비를 적용한다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        self.setFixedWidth(theme.sidebar_width_px())
