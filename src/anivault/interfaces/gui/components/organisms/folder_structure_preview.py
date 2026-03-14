"""Folder structure preview: list of path items."""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.components.molecules.path_box import PathBox


class FolderStructurePreview(QFrame):
    """List of folder path items (resolution + path)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Folder Structure Preview",
                "실제 생성될 디렉토리 샘플과 정렬 구조를 한 곳에서 확인",
                pill_text="Structure",
                pill_color="blue",
            )
        )
        body = QVBoxLayout()
        body.setSpacing(12)
        body.setContentsMargins(18, 18, 18, 18)
        for label, path in [
            ("1080p", r"G:\AniSorted\1080p\2023\장송의 프리렌\Season01"),
            ("1080p", r"G:\AniSorted\1080p\2023\약사의 혼잣말\Season01"),
            ("720p", r"G:\AniSorted\720p\1999\원피스\Season01"),
            ("Unknown", r"G:\AniSorted\Unknown\Unknown\Needs_Review\Season00"),
        ]:
            item = QWidget()
            item_layout = QVBoxLayout(item)
            item_layout.setContentsMargins(14, 14, 14, 14)
            strong = QLabel(label)
            strong.setStyleSheet(theme.list_item_strong())
            item_layout.addWidget(strong)
            item_layout.addWidget(PathBox(path))
            item.setStyleSheet(theme.list_item())
            body.addWidget(item)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
