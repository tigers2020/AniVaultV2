"""execution_card.py

이동 요약 + Move/Undo 등 액션 행.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, Pill
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.themes import get_current_density_key
from anivault.interfaces.gui.themes.responsive import get_profile, scaled_int


class ExecutionCard(QFrame):
    """실행 패널: 요약 텍스트, Pill, 버튼."""

    move_files_clicked = Signal()
    create_folder_tree_clicked = Signal()
    rollback_clicked = Signal()

    def __init__(self, parent=None):
        """요약·Pill·버튼 행을 구성한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).

        Returns:
            None.
        """
        super().__init__(parent)
        profile = get_profile(get_current_density_key())
        body_margin = scaled_int(18, profile.grid_spacing_scale, minimum=12, maximum=28)
        actions_spacing = scaled_int(10, profile.grid_spacing_scale, minimum=8, maximum=14)
        self._status_pill = Pill("Ready", "green")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Execution",
                "최종 이동 실행과 최근 작업 되돌리기를 같은 탭에서 관리",
                right_widget=self._status_pill,
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(body_margin, body_margin, body_margin, body_margin)
        summary_title = QLabel("Move Summary")
        summary_title.setStyleSheet(theme.list_item_strong())
        body.addWidget(summary_title)
        summary_text = QLabel(
            "8,975 files will be moved using resolution, year, Korean title group, and season folder rules."
        )
        summary_text.setStyleSheet(theme.list_item_muted())
        summary_text.setWordWrap(True)
        body.addWidget(summary_text)
        pills = QWidget()
        pills_layout = QHBoxLayout(pills)
        pills_layout.setContentsMargins(0, scaled_int(8, profile.grid_spacing_scale), 0, 0)
        pills_layout.addWidget(Pill("Preview Complete", "green"))
        pills_layout.addWidget(Pill("73 Review Files", "yellow"))
        body.addWidget(pills)
        actions = QHBoxLayout()
        actions.setSpacing(actions_spacing)
        actions.setContentsMargins(0, scaled_int(16, profile.grid_spacing_scale), 0, 0)
        apply_btn = Button("Move Files", "primary")
        apply_btn.clicked.connect(self.move_files_clicked.emit)
        actions.addWidget(apply_btn)
        create_tree_btn = Button("Create Folder Tree Only", "success")
        create_tree_btn.clicked.connect(self.create_folder_tree_clicked.emit)
        actions.addWidget(create_tree_btn)
        undo_btn = Button("Undo Last Move", "danger")
        undo_btn.clicked.connect(self.rollback_clicked.emit)
        actions.addWidget(undo_btn)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def set_status_pill(self, text: str, color: str) -> None:
        """우측 Pill(Ready/Planning 등)을 갱신한다.

        Args:
            self: 이 위젯.
            text: 표시 문자열.
            color: Pill 색 키.

        Returns:
            None.
        """
        self._status_pill.set_text_and_color(text, color)
