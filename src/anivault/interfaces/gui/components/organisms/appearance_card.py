"""appearance_card.py

테마 선택·외형 옵션 카드.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import ComboBox, Label
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.themes import get_current_theme_name, list_themes


class AppearanceCard(QFrame):
    """테마 콤보. 선택 시 theme_changed 시그널."""

    theme_changed = Signal(str)

    def __init__(self, parent=None):
        """테마 목록을 채우고 현재 테마를 선택한다.

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
                "Appearance",
                "앱 테마를 선택하세요. 다크/라이트 모드를 지원합니다.",
                pill_text="Theme",
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        body.addWidget(Label("Theme", "muted"))
        self._theme_combo = ComboBox(self)
        theme_names = list_themes()
        display_names = {"dark": "Dark", "light": "Light"}
        for name in theme_names:
            self._theme_combo.addItem(display_names.get(name, name.title()), name)
        current = get_current_theme_name()
        idx = self._theme_combo.findData(current)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_selected)
        body.addWidget(self._theme_combo)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def _on_theme_selected(self) -> None:
        """현재 콤보 데이터로 theme_changed를보낸다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        idx = self._theme_combo.currentIndex()
        if idx >= 0:
            theme_id = self._theme_combo.itemData(idx)
            if theme_id:
                self.theme_changed.emit(str(theme_id))
