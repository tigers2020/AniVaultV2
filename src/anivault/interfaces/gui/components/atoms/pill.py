"""pill.py

상태 표시용 작은 칩(파랑·초록·노랑·빨강).

Author: Pom Kim
"""

from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class Pill(QLabel):
    """color 키에 맞는 theme.pill 스타일을 쓴다."""

    def __init__(self, text: str = "", color: str = "blue", parent=None):
        """칩 텍스트와 색 변형을 설정한다.

        Args:
            self: 이 위젯.
            text: 표시 문자열.
            color: blue | green | yellow | red.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(text, parent)
        self.setStyleSheet(theme.pill(color))

    def set_text_and_color(self, text: str, color: str) -> None:
        """표시 문자열과 색 키를 바꾼다.

        Args:
            self: 이 Pill.
            text: 새 라벨.
            color: blue | green | yellow | red.

        Returns:
            None.
        """
        self.setText(text)
        self.setStyleSheet(theme.pill(color))
