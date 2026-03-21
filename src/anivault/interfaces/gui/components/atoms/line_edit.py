"""line_edit.py

테마가 적용된 QLineEdit.

Author: Pom Kim
"""

from PySide6.QtWidgets import QLineEdit

from anivault.interfaces.gui import theme


class LineEdit(QLineEdit):
    """placeholder로 초기 문자열을 넣고 line_edit 스타일을 적용한다."""

    def __init__(self, text: str = "", parent=None):
        """플레이스홀더 텍스트를 설정한다.

        Args:
            self: 이 위젯.
            text: placeholderText로 쓸 문자열.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setPlaceholderText(text or "")
        self.setStyleSheet(theme.line_edit())
