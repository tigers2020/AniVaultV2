"""stat_card.py

라벨 + 큰 숫자 형태 통계 카드.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label


class StatCard(QFrame):
    """상단 라벨, 하단 값 라벨."""

    def __init__(self, label_text: str, value: str = "0", parent=None):
        """통계 한 칸을 구성한다.

        Args:
            self: 이 위젯.
            label_text: 지표 이름.
            value: 표시할 값 문자열.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setObjectName("stat_card")
        layout = QVBoxLayout(self)
        body_padding = theme.card_body_padding_px()
        layout.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        layout.setSpacing(theme.panel_header_stack_gap_px())
        self._title_lbl = Label(label_text, "stat")
        layout.addWidget(self._title_lbl)
        value_lbl = Label(value, "default")
        value_lbl.setStyleSheet(theme.stat_card_value())
        layout.addWidget(value_lbl)
        self.setStyleSheet(theme.stat_card())

    def set_title(self, label_text: str) -> None:
        """상단 지표 이름 라벨을 바꾼다.

        Args:
            self: 이 위젯.
            label_text: 새 제목.

        Returns:
            None.
        """
        self._title_lbl.setText(label_text)

    def set_value(self, value: str) -> None:
        """두 번째 라벨(값) 텍스트를 바꾼다.

        Args:
            self: 이 위젯.
            value: 새 값 문자열.

        Returns:
            None.
        """
        layout = self.layout()
        if layout and layout.count() >= 2:
            item = layout.itemAt(1)
            if item is None:
                return
            w = item.widget()
            if isinstance(w, QLabel):
                w.setText(value)
