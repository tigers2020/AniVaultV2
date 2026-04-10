"""form_field.py

라벨 + LineEdit / ComboBox / PathSelectField 조합 필드.

Author: Pom Kim
"""

from collections.abc import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.atoms import ComboBox, Label, LineEdit
from anivault.interfaces.gui.components.molecules.path_select_field import PathSelectField
from anivault.interfaces.gui.i18n import keys as K


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
        self._static_label = label_text
        self._label_updater_fn = label_updater
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        effective_label = label_updater(initial) if label_updater and kind == "line" else label_text
        self._label = Label(effective_label, "muted")
        layout.addWidget(self._label)
        if kind == "combo":
            self._input = self._build_combo_input(layout, initial)
            return
        if kind == "path":
            self._input = self._build_path_input(layout, initial)
            return
        self._input = self._build_line_input(
            layout=layout,
            initial=initial,
            echo_password=echo_password,
        )

    def _build_combo_input(self, layout: QVBoxLayout, initial: str) -> ComboBox:
        combo = ComboBox(self)
        if initial:
            combo.addItem(initial)
        layout.addWidget(combo)
        combo.currentIndexChanged.connect(lambda *_: self.value_changed.emit())
        return combo

    def _build_path_input(self, layout: QVBoxLayout, initial: str) -> PathSelectField:
        path_field = PathSelectField(parent=self, placeholder_key=K.ORG_PATH_FIELD_PLACEHOLDER)
        if initial:
            path_field.set_path(initial)
        layout.addWidget(path_field)
        path_field.path_changed.connect(lambda *_: self.value_changed.emit())
        return path_field

    def _build_line_input(
        self,
        layout: QVBoxLayout,
        initial: str,
        echo_password: bool,
    ) -> LineEdit:
        line = LineEdit(initial, self)
        if echo_password:
            line.setEchoMode(QLineEdit.EchoMode.Password)
        if initial:
            line.setText(initial)
        if self._label_updater_fn is not None:
            line.textChanged.connect(self._on_line_text_for_label)
        layout.addWidget(line)
        line.textChanged.connect(lambda *_: self.value_changed.emit())
        line.editingFinished.connect(lambda *_: self.value_changed.emit())
        return line

    def _on_line_text_for_label(self, text: str) -> None:
        if self._label_updater_fn is not None:
            self._label.setText(self._label_updater_fn(text))

    def apply_static_label(self, text: str) -> None:
        """라벨 업데이터가 없을 때 상단 라벨만 갱신한다."""
        self._static_label = text
        self._refresh_label_display()

    def set_label_updater(self, label_updater: Callable[[str], str] | None) -> None:
        """Path template 등 동적 라벨 함수를 교체하고 현재 값으로 다시 그린다."""
        self._label_updater_fn = label_updater
        self._refresh_label_display()

    def _refresh_label_display(self) -> None:
        if isinstance(self._input, LineEdit) and self._label_updater_fn is not None:
            self._label.setText(self._label_updater_fn(self._input.text()))
        else:
            self._label.setText(self._static_label)

    def retranslate_path_placeholder(self) -> None:
        """kind가 path일 때 플레이스홀더·버튼·다이얼로그 제목을 현재 언어로 맞춘다."""
        if isinstance(self._input, PathSelectField):
            self._input.retranslate_ui()

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
