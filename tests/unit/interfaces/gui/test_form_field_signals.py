"""FormField signal adaptation tests."""

from PySide6.QtWidgets import QApplication

from anivault.interfaces.gui.components.atoms import LineEdit
from anivault.interfaces.gui.components.molecules.form_field import FormField
from anivault.interfaces.gui.components.molecules.path_select_field import PathSelectField


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_form_field_value_changed_ignores_line_edit_signal_args() -> None:
    _ensure_app()
    field = FormField("Name")
    calls: list[str] = []
    field.value_changed.connect(lambda: calls.append("changed"))

    assert isinstance(field._input, LineEdit)
    field._input.textChanged.emit("new value")

    assert calls == ["changed"]


def test_form_field_value_changed_ignores_combo_signal_args() -> None:
    _ensure_app()
    field = FormField("Mode", kind="combo", initial="Auto")
    calls: list[str] = []
    field.value_changed.connect(lambda: calls.append("changed"))

    field._input.currentIndexChanged.emit(0)

    assert calls == ["changed"]


def test_form_field_value_changed_ignores_path_signal_args() -> None:
    _ensure_app()
    field = FormField("Path", kind="path")
    calls: list[str] = []
    field.value_changed.connect(lambda: calls.append("changed"))

    assert isinstance(field._input, PathSelectField)
    field._input.path_changed.emit("F:/Anime")

    assert calls == ["changed"]
