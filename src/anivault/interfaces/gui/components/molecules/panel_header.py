"""panel_header.py

패널 제목·설명·선택적 Pill 또는 우측 위젯.

Author: Pom Kim
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label, Pill


class PanelHeader(QWidget):
    """타이틀, 선택적 설명, 우측 Pill 또는 커스텀 위젯."""

    def __init__(
        self,
        title: str,
        description: str = "",
        pill_text: str = "",
        pill_color: str = "blue",
        right_widget: QWidget | None = None,
        parent=None,
    ):
        """헤더 레이아웃을 구성한다.

        Args:
            self: 이 위젯.
            title: 패널 제목.
            description: 한 줄 말줄임 설명(선택).
            pill_text: 우측 Pill 문구(right_widget 없을 때).
            pill_color: Pill 색 키.
            right_widget: 우측에 넣을 위젯(있으면 Pill 대신).
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        self._description_text = description
        self._desc_lbl: Label | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 0)
        left = QVBoxLayout()
        left.setSpacing(6)
        left.setContentsMargins(0, 0, 0, 0)
        title_lbl = Label(title, "title")
        title_lbl.setStyleSheet(theme.panel_header_title())
        left.addWidget(title_lbl)
        if description:
            desc_lbl = Label(description, "muted")
            desc_lbl.setStyleSheet(theme.panel_header_desc())
            # Prevent long descriptions from overlapping right-side controls.
            # We elide to one line based on available width.
            desc_lbl.setWordWrap(False)
            desc_lbl.setSizePolicy(
                QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            )
            desc_lbl.setMinimumWidth(0)
            left.addWidget(desc_lbl)
            self._desc_lbl = desc_lbl
        layout.addLayout(left, 1)
        if right_widget is not None:
            layout.addWidget(right_widget)
        elif pill_text:
            layout.addWidget(Pill(pill_text, pill_color))

    def resizeEvent(self, event) -> None:
        """크기 변경 시 설명 말줄임을 다시 적용한다.

        Args:
            self: 이 위젯.
            event: Qt 리사이즈 이벤트.

        Returns:
            None.
        """
        super().resizeEvent(event)
        self._apply_description_elide()

    def _apply_description_elide(self) -> None:
        """설명 라벨이 있으면 가용 폭에 맞춰 오른쪽 말줄임을 적용한다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        if self._desc_lbl is None:
            return
        metrics = QFontMetrics(self._desc_lbl.font())
        available = max(0, self._desc_lbl.width() - 2)
        elided = metrics.elidedText(self._description_text, Qt.TextElideMode.ElideRight, available)
        self._desc_lbl.setText(elided)
