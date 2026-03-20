"""Form field: Label + LineEdit, ComboBox, or PathSelectField."""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import ComboBox, Label, LineEdit
from anivault.interfaces.gui.components.molecules.path_select_field import PathSelectField


class FormField(QWidget):
    """Label on top, input below. kind='line' | 'combo' | 'path'."""

    value_changed = Signal()

    _input: ComboBox | LineEdit | PathSelectField

    def __init__(
        self,
        label_text: str,
        kind: str = "line",
        initial: str = "",
        parent: QWidget | None = None,
        *,
        label_updater: Callable[[str], str] | None = None,
        echo_password: bool = False,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        effective_label = label_updater(initial) if label_updater and kind == "line" else label_text
        self._label = Label(effective_label, "muted")
        layout.addWidget(self._label)
        if kind == "combo":
            combo = ComboBox(self)
            if initial:
                combo.addItem(initial)
            layout.addWidget(combo)
            self._input = combo
            combo.currentIndexChanged.connect(self.value_changed.emit)
        elif kind == "path":
            path_field = PathSelectField(placeholder=initial or "폴더 경로", parent=self)
            if initial:
                path_field.set_path(initial)
            layout.addWidget(path_field)
            self._input = path_field
            path_field.path_changed.connect(self.value_changed.emit)
        else:
            line = LineEdit(initial, self)
            if echo_password:
                line.setEchoMode(QLineEdit.EchoMode.Password)
            if initial:
                line.setText(initial)
            if label_updater:
                line.textChanged.connect(lambda t: self._label.setText(label_updater(t)))
            layout.addWidget(line)
            self._input = line
            line.editingFinished.connect(self.value_changed.emit)

    def value(self) -> str:
        if isinstance(self._input, PathSelectField):
            return self._input.path()
        if isinstance(self._input, LineEdit):
            return self._input.text()
        return self._input.currentText() if self._input.count() else ""

    def set_value(self, value: str) -> None:
        if isinstance(self._input, PathSelectField):
            self._input.set_path(value)
        elif isinstance(self._input, LineEdit):
            self._input.setText(value)
        else:
            idx = self._input.findText(value)
            if idx >= 0:
                self._input.setCurrentIndex(idx)
