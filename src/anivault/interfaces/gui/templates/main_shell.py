"""Main shell: Sidebar + Topbar + QStackedWidget(pages area)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.organisms import Sidebar, Topbar


class MainShell(QWidget):
    """Sidebar (fixed width) + main content (topbar + stacked pages)."""

    tab_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._sidebar = Sidebar()
        self._sidebar.tab_clicked.connect(self._on_tab_clicked)
        layout.addWidget(self._sidebar)
        main = QFrame()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(26, 26, 26, 26)
        self._topbar = Topbar()
        main_layout.addWidget(self._topbar)
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, 1)
        layout.addWidget(main, 1)

    def _on_tab_clicked(self, tab_id: str) -> None:
        self._sidebar.set_active_tab(tab_id)
        self.tab_clicked.emit(tab_id)

    def set_topbar_page(self, title: str, description: str) -> None:
        self._topbar.set_page(title, description)

    def add_page(self, widget: QWidget) -> None:
        self._stack.addWidget(widget)

    def set_current_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)

    def topbar(self) -> Topbar:
        return self._topbar

    def sidebar(self) -> Sidebar:
        return self._sidebar
