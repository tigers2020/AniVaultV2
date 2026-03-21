"""view_toggle_bar.py

인라인 콤보 선택 + 패널 토글 버튼 줄.

Author: Pom Kim
"""

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import ComboBox, Label, ViewToggleButton

VIEW_DETAILS = "details"
VIEW_LIST = "list"
VIEW_CONTENT = "content"
VIEW_ICON_XL = "icon_xl"
VIEW_ICON_L = "icon_l"
VIEW_ICON_M = "icon_m"
VIEW_ICON_S = "icon_s"

# 2-stage combo: a "layout" choice that may map to one of the icon sizes.
VIEW_ICON_GROUP = "icon_group"

_ICON_VIEWS: set[str] = {VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S}


def _view_label(key: str) -> str:
    """내부 뷰 키를 콤보에 표시할 한글 라벨로 바꾼다.

    Args:
        key: VIEW_* 상수 문자열.

    Returns:
        한글 라벨. 없으면 key 그대로.
    """
    labels = {
        VIEW_ICON_XL: "아주 큰 아이콘",
        VIEW_ICON_L: "큰 아이콘",
        VIEW_ICON_M: "보통 아이콘",
        VIEW_ICON_S: "작은 아이콘",
        VIEW_LIST: "목록",
        VIEW_DETAILS: "자세히",
        VIEW_CONTENT: "내용",
        VIEW_ICON_GROUP: "아이콘",
    }
    return labels.get(key, key)


class ViewToggleBar(QWidget):
    """PipelineResultPanel 헤더용 인라인 뷰 스위처."""

    view_changed = Signal(str)
    details_pane_changed = Signal(bool)
    preview_pane_changed = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """콤보·토글·시그널을 초기화한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯.

        Returns:
            None.
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._current_view = VIEW_DETAILS
        self._details_pane_checked = False
        self._preview_pane_checked = False

        # Layout selection (details/list/content/icon-group)
        self._layout_combo = ComboBox()
        self._layout_combo.setObjectName("view_toggle_layout_combo")
        for key in (VIEW_DETAILS, VIEW_LIST, VIEW_CONTENT, VIEW_ICON_GROUP):
            self._layout_combo.addItem(_view_label(key), key)

        # Icon size selection (shown only when layout == icon-group)
        self._icon_size_combo = ComboBox()
        self._icon_size_combo.setObjectName("view_toggle_icon_size_combo")
        for key in (VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S):
            self._icon_size_combo.addItem(_view_label(key), key)

        # Pane toggles
        self._details_btn = ViewToggleButton(
            "세부 정보 창",
            checked=self._details_pane_checked,
            object_name="view_toggle_details_pane_btn",
        )

        self._preview_btn = ViewToggleButton(
            "미리 보기 창",
            checked=self._preview_pane_checked,
            object_name="view_toggle_preview_pane_btn",
        )

        # Visual layout
        self._label = Label("보기", "muted")
        self._label.setStyleSheet(theme.label_muted())

        layout.addWidget(self._label)
        layout.addWidget(self._layout_combo)
        layout.addWidget(self._icon_size_combo)
        layout.addWidget(self._details_btn)
        layout.addWidget(self._preview_btn)

        # Set initial UI state without emitting.
        self._sync_ui_from_view(self._current_view)

        # Connect signals after initial setup.
        self._layout_combo.currentIndexChanged.connect(self._on_layout_changed)
        self._icon_size_combo.currentIndexChanged.connect(self._on_icon_size_changed)
        self._details_btn.toggled.connect(self._on_details_pane_toggled)
        self._preview_btn.toggled.connect(self._on_preview_pane_toggled)

    def _sync_icon_size_combo_visibility(self) -> None:
        """아이콘 그룹 레이아웃일 때만 아이콘 크기 콤보를 보인다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        show = self._layout_combo.currentData() == VIEW_ICON_GROUP
        self._icon_size_combo.setVisible(show)

    def _sync_ui_from_view(self, key: str) -> None:
        """뷰 키에 맞춰 콤보 선택만 맞춘다(시그널 없음).

        Args:
            self: 이 위젯.
            key: 현재 뷰 키.

        Returns:
            None.
        """
        with QSignalBlocker(self._layout_combo), QSignalBlocker(self._icon_size_combo):
            if key in _ICON_VIEWS:
                self._layout_combo.setCurrentIndex(self._layout_combo.findData(VIEW_ICON_GROUP))
                self._icon_size_combo.setCurrentIndex(self._icon_size_combo.findData(key))
            else:
                self._layout_combo.setCurrentIndex(self._layout_combo.findData(key))
                # Keep icon selection as-is for when user returns to icon group.

            self._current_view = key
        self._sync_icon_size_combo_visibility()

    def _set_view(self, key: str) -> None:
        """내부 현재 뷰를 갱신하고 view_changed를보낸다.

        Args:
            self: 이 위젯.
            key: 새 뷰 키.

        Returns:
            None.
        """
        if key == self._current_view:
            return
        self._current_view = key
        self.view_changed.emit(key)

    def _on_layout_changed(self, _idx: int) -> None:
        """레이아웃 콤보 변경 시 뷰를 갱신한다.

        Args:
            self: 이 위젯.
            _idx: Qt에서 넘기는 인덱스(미사용).

        Returns:
            None.
        """
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
        """아이콘 크기 콤보 변경 시 아이콘 그룹일 때만 뷰를 갱신한다.

        Args:
            self: 이 위젯.
            _idx: Qt 인덱스(미사용).

        Returns:
            None.
        """
        layout_key = self._layout_combo.currentData()
        if layout_key != VIEW_ICON_GROUP:
            return
        icon_key = self._icon_size_combo.currentData()
        if not isinstance(icon_key, str):
            return
        self._set_view(icon_key)

    def _on_details_pane_toggled(self, checked: bool) -> None:
        """세부 정보 창 토글 상태를 저장·전파한다.

        Args:
            self: 이 위젯.
            checked: 체크 여부.

        Returns:
            None.
        """
        self._details_pane_checked = checked
        self.details_pane_changed.emit(self._details_pane_checked)

    def _on_preview_pane_toggled(self, checked: bool) -> None:
        """미리보기 창 토글 상태를 저장·전파한다.

        Args:
            self: 이 위젯.
            checked: 체크 여부.

        Returns:
            None.
        """
        self._preview_pane_checked = checked
        self.preview_pane_changed.emit(self._preview_pane_checked)

    def set_details_pane_checked(self, checked: bool) -> None:
        """UI만 맞춘다(시그널 없음).

        Args:
            self: 이 위젯.
            checked: 버튼 체크 상태.

        Returns:
            None.
        """
        self._details_pane_checked = checked
        with QSignalBlocker(self._details_btn):
            self._details_btn.setChecked(checked)

    def set_preview_pane_checked(self, checked: bool) -> None:
        """UI만 맞춘다(시그널 없음).

        Args:
            self: 이 위젯.
            checked: 버튼 체크 상태.

        Returns:
            None.
        """
        self._preview_pane_checked = checked
        with QSignalBlocker(self._preview_btn):
            self._preview_btn.setChecked(checked)

    def set_current_view(self, key: str) -> None:
        """외부에서 뷰 키에 맞춰 콤보만 동기화한다(시그널 없음).

        Args:
            self: 이 위젯.
            key: 반영할 뷰 키.

        Returns:
            None.
        """
        self._sync_ui_from_view(key)

    def current_view(self) -> str:
        """현재 선택된 뷰 키를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            뷰 키 문자열.
        """
        return self._current_view

    def details_pane_checked(self) -> bool:
        """세부 정보 창 토글 상태를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            켜짐 여부.
        """
        return self._details_pane_checked

    def preview_pane_checked(self) -> bool:
        """미리보기 창 토글 상태를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            켜짐 여부.
        """
        return self._preview_pane_checked
