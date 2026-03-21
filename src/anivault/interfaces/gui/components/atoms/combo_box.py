"""combo_box.py

테마가 적용된 QComboBox.

Author: Pom Kim
"""

from PySide6.QtWidgets import QComboBox

from anivault.interfaces.gui import theme


class ComboBox(QComboBox):
    """combo_box 테마 스타일시트를 적용한다."""

    def __init__(self, parent=None):
        """콤보 박스를 초기화한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setStyleSheet(theme.combo_box())
