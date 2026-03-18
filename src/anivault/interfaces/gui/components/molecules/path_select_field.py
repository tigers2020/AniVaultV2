"""Path select field: LineEdit + folder browse button."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import Button, LineEdit


class PathSelectField(QWidget):
    """LineEdit + '폴더 선택' button. Uses QFileDialog.getExistingDirectory."""

    path_changed = Signal(str)

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self._edit = LineEdit()
        self._edit.setPlaceholderText(placeholder or "폴더 경로")
        layout.addWidget(self._edit, 1)
        browse = Button("폴더 선택")
        browse.clicked.connect(self._on_browse)
        layout.addWidget(browse)

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self._edit.setText(path)
            self.path_changed.emit(path)

    def path(self) -> str:
        return self._edit.text().strip()

    def set_path(self, path: str) -> None:
        self._edit.setText(path or "")
