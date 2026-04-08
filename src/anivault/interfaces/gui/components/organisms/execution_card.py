"""execution_card.py

이동 요약과 실행/롤백 액션 카드.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.constants.gui.components import (
    EXECUTION_CARD_BUTTON_CREATE_TREE,
    EXECUTION_CARD_BUTTON_MOVE_FILES,
    EXECUTION_CARD_BUTTON_UNDO,
    EXECUTION_CARD_HEADER_DESCRIPTION,
    EXECUTION_CARD_HEADER_TITLE,
    EXECUTION_CARD_PILL_PREVIEW_COMPLETE,
    EXECUTION_CARD_PILL_REVIEW_FILES,
    EXECUTION_CARD_STATUS_READY,
    EXECUTION_CARD_SUMMARY_TEXT,
    EXECUTION_CARD_SUMMARY_TITLE,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, Pill
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.themes import get_current_density_key
from anivault.interfaces.gui.themes.responsive import get_profile, scaled_int


class ExecutionCard(QFrame):
    """실행 요약 카드와 액션 버튼."""

    move_files_clicked = Signal()
    create_folder_tree_clicked = Signal()
    rollback_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        profile = get_profile(get_current_density_key())
        body_margin = scaled_int(18, profile.grid_spacing_scale, minimum=12, maximum=28)
        actions_spacing = scaled_int(10, profile.grid_spacing_scale, minimum=8, maximum=14)
        self._status_pill = Pill(EXECUTION_CARD_STATUS_READY, "green")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                EXECUTION_CARD_HEADER_TITLE,
                EXECUTION_CARD_HEADER_DESCRIPTION,
                right_widget=self._status_pill,
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(body_margin, body_margin, body_margin, body_margin)
        summary_title = QLabel(EXECUTION_CARD_SUMMARY_TITLE)
        summary_title.setStyleSheet(theme.list_item_strong())
        body.addWidget(summary_title)
        summary_text = QLabel(EXECUTION_CARD_SUMMARY_TEXT)
        summary_text.setStyleSheet(theme.list_item_muted())
        summary_text.setWordWrap(True)
        body.addWidget(summary_text)
        pills = QWidget()
        pills_layout = QHBoxLayout(pills)
        pills_layout.setContentsMargins(0, scaled_int(8, profile.grid_spacing_scale), 0, 0)
        pills_layout.addWidget(Pill(EXECUTION_CARD_PILL_PREVIEW_COMPLETE, "green"))
        pills_layout.addWidget(Pill(EXECUTION_CARD_PILL_REVIEW_FILES, "yellow"))
        body.addWidget(pills)
        actions = QHBoxLayout()
        actions.setSpacing(actions_spacing)
        actions.setContentsMargins(0, scaled_int(16, profile.grid_spacing_scale), 0, 0)
        apply_btn = Button(EXECUTION_CARD_BUTTON_MOVE_FILES, "primary")
        apply_btn.clicked.connect(self.move_files_clicked.emit)
        actions.addWidget(apply_btn)
        create_tree_btn = Button(EXECUTION_CARD_BUTTON_CREATE_TREE, "success")
        create_tree_btn.clicked.connect(self.create_folder_tree_clicked.emit)
        actions.addWidget(create_tree_btn)
        undo_btn = Button(EXECUTION_CARD_BUTTON_UNDO, "danger")
        undo_btn.clicked.connect(self.rollback_clicked.emit)
        actions.addWidget(undo_btn)
        body.addLayout(actions)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())

    def set_status_pill(self, text: str, color: str) -> None:
        self._status_pill.set_text_and_color(text, color)
