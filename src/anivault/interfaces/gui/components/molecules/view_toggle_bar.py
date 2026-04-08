"""View toggle bar for pipeline results."""

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.constants.gui.copy import (
    VIEW_LABELS,
    VIEW_TOGGLE_DETAILS_PANE_LABEL,
    VIEW_TOGGLE_LABEL,
)
from anivault.constants.gui.navigation import (
    VIEW_CONTENT,
    VIEW_DETAILS,
    VIEW_ICON_GROUP,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_ICON_XL,
)
from anivault.constants.gui.theme import VIEW_TOGGLE_SPACING_PX
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import ComboBox, Label, ViewToggleButton

_ICON_VIEWS: set[str] = {VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S}

__all__ = [
    "VIEW_DETAILS",
    "VIEW_CONTENT",
    "VIEW_ICON_XL",
    "VIEW_ICON_L",
    "VIEW_ICON_M",
    "VIEW_ICON_S",
    "VIEW_ICON_GROUP",
    "ViewToggleBar",
]


def _view_label(key: str) -> str:
    return VIEW_LABELS.get(key, key)


class ViewToggleBar(QWidget):
    """Layout and detail-pane toggles."""

    view_changed = Signal(str)
    details_pane_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(VIEW_TOGGLE_SPACING_PX)

        self._current_view = VIEW_DETAILS
        self._details_pane_checked = False

        self._layout_combo = ComboBox()
        self._layout_combo.setObjectName("view_toggle_layout_combo")
        for key in (VIEW_DETAILS, VIEW_CONTENT, VIEW_ICON_GROUP):
            self._layout_combo.addItem(_view_label(key), key)

        self._icon_size_combo = ComboBox()
        self._icon_size_combo.setObjectName("view_toggle_icon_size_combo")
        for key in (VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S):
            self._icon_size_combo.addItem(_view_label(key), key)

        self._details_btn = ViewToggleButton(
            VIEW_TOGGLE_DETAILS_PANE_LABEL,
            checked=self._details_pane_checked,
            object_name="view_toggle_details_pane_btn",
        )

        self._label = Label(VIEW_TOGGLE_LABEL, "muted")
        self._label.setStyleSheet(theme.label_muted())

        layout.addWidget(self._label)
        layout.addWidget(self._layout_combo)
        layout.addWidget(self._icon_size_combo)
        layout.addWidget(self._details_btn)

        self._sync_ui_from_view(self._current_view)

        self._layout_combo.currentIndexChanged.connect(self._on_layout_changed)
        self._icon_size_combo.currentIndexChanged.connect(self._on_icon_size_changed)
        self._details_btn.toggled.connect(self._on_details_pane_toggled)

    def _sync_icon_size_combo_visibility(self) -> None:
        show = self._layout_combo.currentData() == VIEW_ICON_GROUP
        self._icon_size_combo.setVisible(show)

    def _sync_ui_from_view(self, key: str) -> None:
        with QSignalBlocker(self._layout_combo), QSignalBlocker(self._icon_size_combo):
            if key in _ICON_VIEWS:
                self._layout_combo.setCurrentIndex(self._layout_combo.findData(VIEW_ICON_GROUP))
                self._icon_size_combo.setCurrentIndex(self._icon_size_combo.findData(key))
            else:
                self._layout_combo.setCurrentIndex(self._layout_combo.findData(key))
            self._current_view = key
        self._sync_icon_size_combo_visibility()

    def _set_view(self, key: str) -> None:
        if key == self._current_view:
            return
        self._current_view = key
        self.view_changed.emit(key)

    def _on_layout_changed(self, _idx: int) -> None:
        key = self._layout_combo.currentData()
        if not isinstance(key, str):
            return
        self._sync_icon_size_combo_visibility()
        if key == VIEW_ICON_GROUP:
            icon_key = self._icon_size_combo.currentData()
            if not isinstance(icon_key, str):
                return
            self._set_view(icon_key)
        else:
            self._set_view(key)

    def _on_icon_size_changed(self, _idx: int) -> None:
        if self._layout_combo.currentData() != VIEW_ICON_GROUP:
            return
        icon_key = self._icon_size_combo.currentData()
        if not isinstance(icon_key, str):
            return
        self._set_view(icon_key)

    def _on_details_pane_toggled(self, checked: bool) -> None:
        self._details_pane_checked = checked
        self.details_pane_changed.emit(self._details_pane_checked)

    def set_details_pane_checked(self, checked: bool) -> None:
        with QSignalBlocker(self._details_btn):
            self._details_btn.setChecked(checked)
        self._details_pane_checked = checked

    def set_view(self, key: str) -> None:
        self._sync_ui_from_view(key)

    def set_current_view(self, key: str) -> None:
        self.set_view(key)

    def current_view(self) -> str:
        return self._current_view

    def details_pane_checked(self) -> bool:
        return self._details_pane_checked
