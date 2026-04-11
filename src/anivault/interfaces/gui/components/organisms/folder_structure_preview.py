"""folder_structure_preview.py

폴더 구조 샘플 경로 목록.

Author: Pom Kim
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.components.molecules.path_box import PathBox


class FolderStructurePreview(QFrame):
    """해상도 라벨 + PathBox 항목 리스트."""

    def __init__(self, parent=None):
        """데모 경로 블록을 채운다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
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
        body.setSpacing(theme.inline_control_gap_px())
        body_pad = theme.card_body_padding_px()
        body.setContentsMargins(body_pad, body_pad, body_pad, body_pad)
        for label, path in [
            ("FHD", r"G:\AniSorted\FHD\2023\장송의 프리렌\Season01"),
            ("FHD", r"G:\AniSorted\FHD\2023\약사의 혼잣말\Season01"),
            ("HD", r"G:\AniSorted\HD\1999\원피스\Season01"),
            ("Unknown", r"G:\AniSorted\Unknown\Unknown\Needs_Review\Season00"),
        ]:
            item = QWidget()
            item_layout = QVBoxLayout(item)
            item_pad = theme.settings_section_gap_px()
            item_layout.setContentsMargins(item_pad, item_pad, item_pad, item_pad)
            strong = QLabel(label)
            strong.setStyleSheet(theme.list_item_strong())
            item_layout.addWidget(strong)
            item_layout.addWidget(PathBox(path))
            item.setStyleSheet(theme.list_item())
            body.addWidget(item)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
