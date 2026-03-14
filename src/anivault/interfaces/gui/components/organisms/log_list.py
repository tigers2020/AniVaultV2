"""Log list: Recent Activity (time + message)."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget, QLabel

from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui import theme


class LogList(QFrame):
    """Scrollable list of log entries (time + message)."""

    def __init__(self, parent=None):
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
        self._list_layout.setSpacing(12)
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
        item = QWidget()
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(14, 14, 14, 14)
        strong = QLabel(time_str)
        strong.setStyleSheet(theme.list_item_strong())
        item_layout.addWidget(strong)
        muted = QLabel(message)
        muted.setStyleSheet(theme.list_item_muted())
        muted.setWordWrap(True)
        item_layout.addWidget(muted)
        item.setStyleSheet(theme.list_item())
        self._list_layout.insertWidget(0, item)
