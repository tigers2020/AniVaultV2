"""button.py

스타일 변형(default, primary, success, warn, danger)을 지원하는 QPushButton 래퍼.

Author: Pom Kim
"""

from PySide6.QtWidgets import QPushButton


class Button(QPushButton):
    """objectName으로 변형을 구분하는 스타일 버튼."""

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        """버튼 텍스트·변형·부모를 설정한다.

        Args:
            self: 이 위젯.
            text: 버튼 라벨.
            variant: default 외에는 objectName으로 설정.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(text, parent)
        if variant != "default":
            self.setObjectName(variant)
