"""View toggle bar: Windows Explorer-style layout switcher."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QMenu, QToolButton, QWidget

from anivault.interfaces.gui import theme

VIEW_DETAILS = "details"
VIEW_LIST = "list"
VIEW_TILES = "tiles"
VIEW_CONTENT = "content"
VIEW_ICON_XL = "icon_xl"
VIEW_ICON_L = "icon_l"
VIEW_ICON_M = "icon_m"
VIEW_ICON_S = "icon_s"

VIEW_ORDER = [
    VIEW_ICON_XL,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_LIST,
    VIEW_DETAILS,
    VIEW_TILES,
    VIEW_CONTENT,
]


def _view_label(key: str) -> str:
    labels = {
        VIEW_ICON_XL: "아주 큰 아이콘",
        VIEW_ICON_L: "큰 아이콘",
        VIEW_ICON_M: "보통 아이콘",
        VIEW_ICON_S: "작은 아이콘",
        VIEW_LIST: "목록",
        VIEW_DETAILS: "자세히",
        VIEW_TILES: "타일",
        VIEW_CONTENT: "내용",
    }
    return labels.get(key, key)


class ViewToggleBar(QWidget):
    """Windows Explorer-style view switcher. Dropdown menu with layout options."""

    view_changed = Signal(str)
    details_pane_changed = Signal(bool)
    preview_pane_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._btn = QToolButton()
        self._btn.setText("≡ 보기")
        self._btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._btn.setStyleSheet(theme.view_toggle_button())
        layout.addWidget(self._btn)

        self._current_view = VIEW_DETAILS
        self._details_pane_checked = False
        self._preview_pane_checked = False

        menu = QMenu(self)
        menu.setStyleSheet(theme.view_toggle_menu())

        # Icon sizes group
        icon_group = menu.addAction("아이콘 크기")
        icon_group.setEnabled(False)
        self._actions: dict[str, QAction] = {}
        for key in (VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S):
            a = menu.addAction(_view_label(key), lambda k=key: self._set_view(k))
            if a is not None:
                a.setCheckable(True)
                a.setData(key)
                if key == self._current_view:
                    a.setChecked(True)
                self._actions[key] = a

        menu.addSeparator()

        # List/details group
        list_group = menu.addAction("목록 및 세부 정보")
        if list_group is not None:
            list_group.setEnabled(False)
        for key in (VIEW_LIST, VIEW_DETAILS, VIEW_TILES, VIEW_CONTENT):
            a = menu.addAction(_view_label(key), lambda k=key: self._set_view(k))
            if a is not None:
                a.setCheckable(True)
                a.setData(key)
                if key == self._current_view:
                    a.setChecked(True)
                self._actions[key] = a

        menu.addSeparator()

        # Pane toggles
        pane_group = menu.addAction("창 표시")
        if pane_group is not None:
            pane_group.setEnabled(False)
        details_action = menu.addAction("세부 정보 창", self._toggle_details_pane)
        preview_action = menu.addAction("미리 보기 창", self._toggle_preview_pane)
        if details_action is not None:
            details_action.setCheckable(True)
            details_action.setChecked(self._details_pane_checked)
        if preview_action is not None:
            preview_action.setCheckable(True)
            preview_action.setChecked(self._preview_pane_checked)

        self._menu = menu
        self._details_action: QAction | None = details_action
        self._preview_action: QAction | None = preview_action
        self._btn.setMenu(menu)

    def _set_view(self, key: str) -> None:
        self._current_view = key
        for k, a in self._actions.items():
            a.setChecked(k == key)
        self.view_changed.emit(key)

    def _toggle_details_pane(self) -> None:
        if self._details_action is not None:
            self._details_pane_checked = self._details_action.isChecked()
        self.details_pane_changed.emit(self._details_pane_checked)

    def _toggle_preview_pane(self) -> None:
        if self._preview_action is not None:
            self._preview_pane_checked = self._preview_action.isChecked()
        self.preview_pane_changed.emit(self._preview_pane_checked)

    def set_details_pane_checked(self, checked: bool) -> None:
        self._details_pane_checked = checked
        if self._details_action is not None:
            self._details_action.setChecked(checked)

    def set_preview_pane_checked(self, checked: bool) -> None:
        self._preview_pane_checked = checked
        if self._preview_action is not None:
            self._preview_action.setChecked(checked)

    def set_current_view(self, key: str) -> None:
        """Update UI to reflect current view. Does not emit signal."""
        self._current_view = key
        if key in self._actions:
            for k, a in self._actions.items():
                a.setChecked(k == key)
