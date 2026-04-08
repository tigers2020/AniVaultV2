"""path_select_field.py

LineEdit + browse button for selecting a folder path.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget

from anivault.constants.gui.components import (
    PATH_SELECT_FIELD_BROWSE_BUTTON,
    PATH_SELECT_FIELD_DIALOG_TITLE,
    PATH_SELECT_FIELD_PLACEHOLDER,
)
from anivault.interfaces.gui.components.atoms import Button, LineEdit


class PathSelectField(QWidget):
    """Path input field backed by QFileDialog.getExistingDirectory."""

    path_changed = Signal(str)

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._edit = LineEdit()
        self._edit.setPlaceholderText(placeholder or PATH_SELECT_FIELD_PLACEHOLDER)
        layout.addWidget(self._edit, 1)
        browse = Button(PATH_SELECT_FIELD_BROWSE_BUTTON)
        browse.clicked.connect(self._on_browse)
        layout.addWidget(browse)
        self._edit.textChanged.connect(lambda _t: self._emit_path_changed())
        self._edit.editingFinished.connect(self._emit_path_changed)

    def _emit_path_changed(self) -> None:
        self.path_changed.emit(self.path())

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, PATH_SELECT_FIELD_DIALOG_TITLE)
        if path:
            self._edit.setText(path)
            self._emit_path_changed()

    def path(self) -> str:
        return self._edit.text().strip()

    def set_path(self, path: str) -> None:
        self._edit.setText(path or "")
