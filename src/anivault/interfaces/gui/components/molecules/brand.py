"""brand.py

Badge + 제목 + 부제로 브랜드 블록을 구성한다.

Author: Pom Kim
"""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Badge, Label
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n import translate


class Brand(QWidget):
    """로고 배지와 타이틀·서브타이틀 가로 배치."""

    def __init__(self, parent=None):
        """브랜드 문구를 배치한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        gap = theme.inline_control_gap_px()
        layout.setSpacing(gap)
        layout.setContentsMargins(gap, gap, gap, gap)
        badge = Badge("A", 42)
        layout.addWidget(badge)
        right = QVBoxLayout()
        right.setSpacing(theme.compact_gap_px())
        right.setContentsMargins(0, 0, 0, 0)
        self._title_label = Label(translate(K.SHELL_BRAND_TITLE), "title")
        self._title_label.setStyleSheet(theme.brand_title())
        right.addWidget(self._title_label)
        self._subtitle_label = Label(translate(K.SHELL_BRAND_SUBTITLE), "muted")
        self._subtitle_label.setStyleSheet(theme.brand_subtitle())
        right.addWidget(self._subtitle_label)
        layout.addLayout(right, 1)

    def retranslate_ui(self) -> None:
        self._title_label.setText(translate(K.SHELL_BRAND_TITLE))
        self._subtitle_label.setText(translate(K.SHELL_BRAND_SUBTITLE))
