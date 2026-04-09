"""settings_actions_card.py

설정 Save/Reset/Load 액션 바를 카드로 감쌈.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, SettingsActionBar


class SettingsActionsCard(QFrame):
    """PanelHeader + SettingsActionBar."""

    def __init__(self, parent=None):
        """헤더와 액션 바를 넣는다.

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
                "Settings",
                "저장·로드·초기화",
                pill_text="Actions",
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        self._action_bar = SettingsActionBar()
        body.addWidget(self._action_bar)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def action_bar(self) -> SettingsActionBar:
        """시그널 연결용 SettingsActionBar를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            내부 SettingsActionBar.
        """
        return self._action_bar
