"""Form field: Label + LineEdit or ComboBox."""

from PySide6.QtWidgets import QWidget, QVBoxLayout

from anivault.interfaces.gui.components.atoms import ComboBox, Label, LineEdit


class FormField(QWidget):
    """Label on top, input below. kind='line' | 'combo'."""

    def __init__(
        self,
        label_text: str,
        kind: str = "line",
        initial: str = "",
        parent=None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(Label(label_text, "muted"))
        if kind == "combo":
            self._input = ComboBox(self)
            if initial:
                self._input.addItem(initial)
            layout.addWidget(self._input)
        else:
            self._input = LineEdit(initial, self)
            if initial:
                self._input.setText(initial)
            layout.addWidget(self._input)

    def value(self) -> str:
        if isinstance(self._input, LineEdit):
            return self._input.text()
        return self._input.currentText() if self._input.count() else ""

    def set_value(self, value: str) -> None:
        if isinstance(self._input, LineEdit):
            self._input.setText(value)
        else:
            idx = self._input.findText(value)
            if idx >= 0:
                self._input.setCurrentIndex(idx)
