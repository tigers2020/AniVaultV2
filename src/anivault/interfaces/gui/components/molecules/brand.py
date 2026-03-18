"""Brand: Badge + title + subtitle (AniVault V2)."""

from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Badge, Label


class Brand(QWidget):
    """Logo badge plus title and subtitle."""

    def __init__(
        self,
        title: str = "AniVault V2",
        subtitle: str = "Parse → TMDB 한글 제목 → 구조화 이동",
        parent=None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        badge = Badge("A", 42)
        layout.addWidget(badge)
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)
        title_label = Label(title, "title")
        title_label.setStyleSheet(theme.brand_title())
        right.addWidget(title_label)
        sub = Label(subtitle, "muted")
        sub.setStyleSheet(theme.brand_subtitle())
        right.addWidget(sub)
        layout.addLayout(right, 1)
