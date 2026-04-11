"""path_select_field.py

LineEdit + browse button for selecting a folder path.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, LineEdit
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


class PathSelectField(QWidget):
    """Path input field backed by QFileDialog.getExistingDirectory."""

    path_changed = Signal(str)

    def __init__(
        self,
        parent=None,
        *,
        placeholder_key: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._placeholder_key = placeholder_key or K.ORG_PATH_FIELD_PLACEHOLDER
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(theme.layout_spacing_sm_px())
        self._edit = LineEdit()
        self._edit.setPlaceholderText(translate(self._placeholder_key))
        layout.addWidget(self._edit, 1)
        self._browse_btn = Button(translate(K.ORG_PATH_FIELD_BROWSE))
        self._browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self._browse_btn)
        self._dialog_title = translate(K.ORG_PATH_FIELD_DIALOG_TITLE)
        self._edit.textChanged.connect(lambda _t: self._emit_path_changed())
        self._edit.editingFinished.connect(self._emit_path_changed)
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._edit.setPlaceholderText(translate(self._placeholder_key))
        self._browse_btn.setText(translate(K.ORG_PATH_FIELD_BROWSE))
        self._dialog_title = translate(K.ORG_PATH_FIELD_DIALOG_TITLE)

    def _emit_path_changed(self) -> None:
        self.path_changed.emit(self.path())

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, self._dialog_title)
        if path:
            self._edit.setText(path)
            self._emit_path_changed()

    def path(self) -> str:
        return self._edit.text().strip()

    def set_path(self, path: str) -> None:
        self._edit.setText(path or "")
