"""brand.py

Badge + 제목 + 부제로 브랜드 블록을 구성한다.

Author: Pom Kim
"""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Badge, Label


class Brand(QWidget):
    """로고 배지와 타이틀·서브타이틀 가로 배치."""

    def __init__(
        self,
        title: str = "AniVault V2",
        subtitle: str = "Parse → TMDB 한글 제목 → 구조화 이동",
        parent=None,
    ):
        """브랜드 문구를 배치한다.

        Args:
            self: 이 위젯.
            title: 메인 제목.
            subtitle: 부제 설명.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        badge = Badge("A", 42)
        layout.addWidget(badge)
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)
        title_label = Label(title, "title")
        title_label.setStyleSheet(theme.brand_title())
        right.addWidget(title_label)
        sub = Label(subtitle, "muted")
        sub.setStyleSheet(theme.brand_subtitle())
        right.addWidget(sub)
        layout.addLayout(right, 1)
