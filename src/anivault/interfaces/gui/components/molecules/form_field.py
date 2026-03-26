"""form_field.py

라벨 + LineEdit / ComboBox / PathSelectField 조합 필드.

Author: Pom Kim
"""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import ComboBox, Label, LineEdit
from anivault.interfaces.gui.components.molecules.path_select_field import PathSelectField


class FormField(QWidget):
    """상단 라벨, 하단 입력. kind는 line | combo | path."""

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
        """입력 종류에 따라 위젯을 구성하고 시그널을 연결한다.

        Args:
            self: 이 위젯.
            label_text: 라벨 문자열.
            kind: line | combo | path.
            initial: 초기값·플레이스홀더.
            parent: 부모 위젯.
            label_updater: line일 때 텍스트에 따라 라벨을 바꾸는 함수.
            echo_password: line일 때 비밀번호 에코 모드.

        Returns:
            None.
        """
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
            line.textChanged.connect(self.value_changed.emit)
            line.editingFinished.connect(self.value_changed.emit)

    def value(self) -> str:
        """현재 입력 값을 문자열로 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            path/line/combo에 따른 텍스트.
        """
        if isinstance(self._input, PathSelectField):
            return self._input.path()
        if isinstance(self._input, LineEdit):
            return self._input.text()
        return self._input.currentText() if self._input.count() else ""

    def set_value(self, value: str) -> None:
        """입력 위젯에 값을 설정한다.

        Args:
            self: 이 위젯.
            value: 설정할 문자열.

        Returns:
            None.
        """
        if isinstance(self._input, PathSelectField):
            self._input.set_path(value)
        elif isinstance(self._input, LineEdit):
            self._input.setText(value)
        else:
            idx = self._input.findText(value)
            if idx >= 0:
                self._input.setCurrentIndex(idx)
