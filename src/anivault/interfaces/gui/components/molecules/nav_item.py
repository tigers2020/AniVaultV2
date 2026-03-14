"""Nav item: tab button with tab_id for switching."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton

from anivault.interfaces.gui import theme


class NavItem(QPushButton):
    """Tab button. Emits tab_id when clicked."""

    tab_clicked = Signal(str)

    def __init__(self, label: str, tab_id: str, parent=None):
        super().__init__(label, parent)
        self._tab_id = tab_id
        self.clicked.connect(self._on_click)
        self.setStyleSheet(theme.nav_item())
        self.setCheckable(True)

    def _on_click(self) -> None:
        self.tab_clicked.emit(self._tab_id)

    @property
    def tab_id(self) -> str:
        return self._tab_id
