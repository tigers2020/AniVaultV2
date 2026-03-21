"""label.py

stat-label, muted, title 등 테마 변형 QLabel.

Author: Pom Kim
"""

from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class Label(QLabel):
    """variant에 따라 theme 스타일시트를 적용하는 라벨."""

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        """라벨 텍스트·시각 변형을 설정한다.

        Args:
            self: 이 위젯.
            text: 표시 문자열.
            variant: default | muted | stat | title.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(text, parent)
        if variant == "muted":
            self.setStyleSheet(theme.label_muted())
        elif variant == "stat":
            self.setStyleSheet(theme.label_stat())
        elif variant == "title":
            self.setStyleSheet(theme.label_title())
