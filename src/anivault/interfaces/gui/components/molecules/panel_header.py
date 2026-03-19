"""Panel header: title + description + optional Pill or right widget."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label, Pill


class PanelHeader(QWidget):
    """Title, optional description, and optional right-side pill or widget."""

    def __init__(
        self,
        title: str,
        description: str = "",
        pill_text: str = "",
        pill_color: str = "blue",
        right_widget: QWidget | None = None,
        parent=None,
    ):
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
        super().resizeEvent(event)
        self._apply_description_elide()

    def _apply_description_elide(self) -> None:
        if self._desc_lbl is None:
            return
        metrics = QFontMetrics(self._desc_lbl.font())
        available = max(0, self._desc_lbl.width() - 2)
        elided = metrics.elidedText(self._description_text, Qt.TextElideMode.ElideRight, available)
        self._desc_lbl.setText(elided)
