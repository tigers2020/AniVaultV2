"""view_toggle_button.py

뷰/패널 토글용 체크 가능한 QToolButton.

Author: Pom Kim
"""

from PySide6.QtWidgets import QToolButton

from anivault.interfaces.gui import theme


class ViewToggleButton(QToolButton):
    """view_toggle_button 테마를 쓰는 작은 토글 버튼."""

    def __init__(
        self,
        text: str,
        checked: bool = False,
        object_name: str | None = None,
        parent=None,
    ) -> None:
        """텍스트·체크 상태·objectName을 설정한다.

        Args:
            self: 이 위젯.
            text: 버튼 라벨.
            checked: 초기 체크 여부.
            object_name: QSS 타깃용 objectName. None이면 생략.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setChecked(checked)
        if object_name:
            self.setObjectName(object_name)
        self.setStyleSheet(theme.view_toggle_button())
