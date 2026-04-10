"""nav_item.py

탭 전환용 버튼. 클릭 시 tab_id 시그널을보낸다.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton

from anivault.interfaces.gui import theme


class NavItem(QPushButton):
    """체크 가능한 탭 버튼."""

    tab_clicked = Signal(str)

    def __init__(self, label: str, tab_id: str, parent=None):
        """라벨·탭 식별자·스타일을 설정한다.

        Args:
            self: 이 위젯.
            label: 버튼에 보이는 문자열.
            tab_id: tab_clicked에 실릴 ID.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(label, parent)
        self._tab_id = tab_id
        self.clicked.connect(self._on_click)
        self.setStyleSheet(theme.nav_item())
        self.setCheckable(True)

    def _on_click(self) -> None:
        """클릭 시 tab_clicked로 tab_id를보낸다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        self.tab_clicked.emit(self._tab_id)

    @property
    def tab_id(self) -> str:
        """이 내비 항목의 탭 식별자.

        Args:
            self: 이 위젯.

        Returns:
            tab_id 문자열.
        """
        return self._tab_id

    def set_label_text(self, text: str) -> None:
        """Update visible button label (e.g. after language change)."""
        self.setText(text)
