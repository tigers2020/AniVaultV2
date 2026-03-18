"""Settings actions card: Save/Reset/Load bar (organism)."""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader, SettingsActionBar


class SettingsActionsCard(QFrame):
    """Card with settings action buttons. PanelHeader + SettingsActionBar."""

    def __init__(self, parent=None):
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
        body.setContentsMargins(18, 18, 18, 18)
        self._action_bar = SettingsActionBar()
        body.addWidget(self._action_bar)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def action_bar(self) -> SettingsActionBar:
        """Return the SettingsActionBar for signal wiring."""
        return self._action_bar
