"""Label: stat-label, muted, or title."""

from PySide6.QtWidgets import QLabel

from anivault.interfaces.gui import theme


class Label(QLabel):
    """Styled label. variant: 'default' | 'muted' | 'stat' | 'title'."""

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        super().__init__(text, parent)
        if variant == "muted":
            self.setStyleSheet(theme.label_muted())
        elif variant == "stat":
            self.setStyleSheet(theme.label_stat())
        elif variant == "title":
            self.setStyleSheet(theme.label_title())
