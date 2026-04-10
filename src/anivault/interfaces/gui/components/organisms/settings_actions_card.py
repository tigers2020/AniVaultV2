"""settings_actions_card.py

설정 Save/Reset/Load 액션 바를 카드로 감쌈.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, SettingsActionBar
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


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
        self._header = PanelHeader(
            translate(K.SETTINGS_ACTIONS_CARD_TITLE),
            translate(K.SETTINGS_ACTIONS_CARD_DESC),
            pill_text=translate(K.SETTINGS_ACTIONS_CARD_PILL),
            pill_color="blue",
        )
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body_padding = theme.settings_card_body_padding_px()
        body.setContentsMargins(body_padding, body_padding, body_padding, body_padding)
        body.setSpacing(theme.settings_section_gap_px())
        self._action_bar = SettingsActionBar()
        body.addWidget(self._action_bar)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(K.SETTINGS_ACTIONS_CARD_TITLE),
            translate(K.SETTINGS_ACTIONS_CARD_DESC),
            pill_text=translate(K.SETTINGS_ACTIONS_CARD_PILL),
        )
        self._action_bar.retranslate_ui()

    def action_bar(self) -> SettingsActionBar:
        """시그널 연결용 SettingsActionBar를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            내부 SettingsActionBar.
        """
        return self._action_bar
