"""topbar.py

페이지 제목·설명 줄.

Author: Pom Kim
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme


class Topbar(QWidget):
    """페이지 타이틀·부제."""

    def __init__(self, parent=None):
        """레이아웃을 구성한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 22)
        left = QVBoxLayout()
        left.setSpacing(6)
        self._title = QLabel("Organizer")
        self._title.setStyleSheet(theme.topbar_title())
        left.addWidget(self._title)
        self._desc = QLabel(
            "폴더 스캔부터 한글 제목 그룹 확정과 최종 경로 미리보기까지 한 화면에서 처리"
        )
        self._desc.setStyleSheet(theme.topbar_desc())
        self._desc.setWordWrap(True)
        left.addWidget(self._desc)
        layout.addLayout(left, 1)

    def set_page(self, title: str, description: str) -> None:
        """제목·설명 라벨을 바꾼다.

        Args:
            self: 이 위젯.
            title: 새 제목.
            description: 새 설명.

        Returns:
            None.
        """
        self._title.setText(title)
        self._desc.setText(description)
