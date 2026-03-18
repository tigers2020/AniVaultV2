"""Form field: Label + LineEdit or ComboBox."""

from PySide6.QtWidgets import QVBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import ComboBox, Label, LineEdit


class FormField(QWidget):
    """Label on top, input below. kind='line' | 'combo'."""

    _input: ComboBox | LineEdit

    def __init__(
        self,
        label_text: str,
        kind: str = "line",
        initial: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(Label(label_text, "muted"))
        if kind == "combo":
            combo = ComboBox(self)
            if initial:
                combo.addItem(initial)
            layout.addWidget(combo)
            self._input = combo
        else:
            line = LineEdit(initial, self)
            if initial:
                line.setText(initial)
            layout.addWidget(line)
            self._input = line

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
