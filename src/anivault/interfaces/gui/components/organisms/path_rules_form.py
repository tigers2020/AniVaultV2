"""Path rules form: target root, path template, unknown resolution/group."""

from PySide6.QtWidgets import QFrame, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import FormField, PanelHeader


class PathRulesForm(QFrame):
    """Path rules panel fields."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(PanelHeader("Path Rules", "최종 출력 구조와 기본값 설정"))
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
        body.addWidget(FormField("Target root folder", "line", "G:/AniSorted"))
        body.addWidget(
            FormField(
                "Path template",
                "line",
                r"{target}\{resolution}\{year}\{korean_title_group}\Season{season:02}\{original_filename}",
            )
        )
        body.addWidget(FormField("Unknown resolution", "line", "Unknown"))
        body.addWidget(FormField("Unknown group folder", "line", "Needs_Review"))
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
