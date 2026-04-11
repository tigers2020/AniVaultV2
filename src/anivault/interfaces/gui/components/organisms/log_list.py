"""log_list.py

최근 활동(시간 + 메시지) 스크롤 목록.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader


class LogList(QFrame):
    """로그 항목을 위에서 삽입하는 스크롤 리스트."""

    def __init__(self, parent=None):
        """데모 항목으로 목록을 채운다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Recent Activity",
                "스캔, parse, TMDB 조회, 계획 생성 로그를 실행과 함께 확인",
                pill_text="Log View",
                pill_color="blue",
            )
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setSpacing(theme.inline_control_gap_px())
        scroll.setWidget(self._container)
        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())
        for time_str, msg in [
            ("[12:55:08]", "Folder scan started for G:/Animations"),
            ("[12:56:42]", "Filename parse completed for 9,048 files"),
            ("[12:57:10]", "Parse title groups created: 412"),
            ("[12:57:28]", "TMDB Korean title lookup resolved 8,918 files"),
            ("[12:57:45]", "Structured move plan generated"),
        ]:
            self.append_entry(time_str, msg)

    def append_entry(self, time_str: str, message: str) -> None:
        """새 로그 블록을 목록 맨 위에 삽입한다.

        Args:
            self: 이 위젯.
            time_str: 시간/타임스탬프 줄.
            message: 본문 메시지.

        Returns:
            None.
        """
        item = QWidget()
        item_layout = QVBoxLayout(item)
        pad = theme.settings_section_gap_px()
        item_layout.setContentsMargins(pad, pad, pad, pad)
        strong = QLabel(time_str)
        strong.setStyleSheet(theme.list_item_strong())
        item_layout.addWidget(strong)
        muted = QLabel(message)
        muted.setStyleSheet(theme.list_item_muted())
        muted.setWordWrap(True)
        item_layout.addWidget(muted)
        item.setStyleSheet(theme.list_item())
        self._list_layout.insertWidget(0, item)
