"""path_box.py

모노스페이스·마우스로 선택 가능한 경로 표시 QLabel.

Author: Pom Kim
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class PathBox(QLabel):
    """읽기 전용 경로 텍스트. 복사를 위해 선택 가능."""

    def __init__(self, path: str = "", parent=None):
        """경로 문자열과 스타일을 설정한다.

        Args:
            self: 이 위젯.
            path: 초기 표시 경로.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(path or "", parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setStyleSheet(theme.path_box())

    def set_path(self, path: str) -> None:
        """표시 경로를 바꾼다.

        Args:
            self: 이 위젯.
            path: 새 경로 문자열.

        Returns:
            None.
        """
        self.setText(path)
