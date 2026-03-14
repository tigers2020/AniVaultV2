"""Panel header: title + description + optional Pill."""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from anivault.interfaces.gui.components.atoms import Label, Pill
from anivault.interfaces.gui import theme


class PanelHeader(QWidget):
    """Title, optional description, and optional right-side pill."""

    def __init__(
        self,
        title: str,
        description: str = "",
        pill_text: str = "",
        pill_color: str = "blue",
        parent=None,
    ):
        super().__init__(parent)
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
            left.addWidget(desc_lbl)
        layout.addLayout(left, 1)
        if pill_text:
            layout.addWidget(Pill(pill_text, pill_color))
