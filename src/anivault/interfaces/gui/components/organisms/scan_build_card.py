"""Scan/Build card: Source/Target inputs + TMDB/Unknown selects + Scan·Build buttons."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout

from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.components.atoms import Button, LineEdit, ComboBox
from anivault.interfaces.gui import theme


class ScanBuildCard(QFrame):
    """Pipeline controls: inputs and step buttons. Buttons only collect input + emit; no step logic."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Scan and Build Plan",
                "입력 폴더 스캔, parse, TMDB 조회, 한글 제목 그룹, 최종 이동 경로 생성을 Settings 탭에서 관리",
                pill_text="Pipeline Controls",
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setSpacing(10)
        self._source = LineEdit()
        self._source.setPlaceholderText("Source: G:/Animations; D:/Incoming_Downloads")
        toolbar_layout.addWidget(self._source)
        self._target = LineEdit()
        self._target.setPlaceholderText("Target Root: G:/AniSorted")
        toolbar_layout.addWidget(self._target)
        self._tmdb_mode = ComboBox()
        self._tmdb_mode.addItems(["TMDB TV Search", "TMDB Multi Search"])
        toolbar_layout.addWidget(self._tmdb_mode)
        self._unknown_mode = ComboBox()
        self._unknown_mode.addItems(["Unknown to Needs_Review", "Leave unknown in source"])
        toolbar_layout.addWidget(self._unknown_mode)
        body.addWidget(toolbar)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(Button("1. Scan Folder", "primary"))
        action_row.addWidget(Button("2. Parse Names"))
        action_row.addWidget(Button("3. Query TMDB"))
        action_row.addWidget(Button("4. Build Move Plan", "warn"))
        body.addLayout(action_row)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
