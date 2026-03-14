"""Path display: monospace, selectable (QLabel)."""

from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from anivault.interfaces.gui import theme


class PathBox(QLabel):
    """Read-only path text; selectable for copy."""

    def __init__(self, path: str = "", parent=None):
        super().__init__(path or "", parent)
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setStyleSheet(theme.path_box())

    def set_path(self, path: str) -> None:
        self.setText(path)
