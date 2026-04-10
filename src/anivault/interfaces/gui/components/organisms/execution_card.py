"""execution_card.py

이동 요약과 실행/롤백 액션 카드.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, Pill
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K
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
        self._status_pill = Pill(translate(K.EXEC_CARD_STATUS_READY), "green")
        self._header = PanelHeader(
            translate(K.EXEC_CARD_HEADER_TITLE),
            translate(K.EXEC_CARD_HEADER_DESC),
            right_widget=self._status_pill,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._header)
        body = QVBoxLayout()
        body.setContentsMargins(body_margin, body_margin, body_margin, body_margin)
        self._summary_title = QLabel(translate(K.EXEC_CARD_SUMMARY_TITLE))
        self._summary_title.setStyleSheet(theme.list_item_strong())
        body.addWidget(self._summary_title)
        self._summary_text = QLabel(translate(K.EXEC_CARD_SUMMARY_TEXT))
        self._summary_text.setStyleSheet(theme.list_item_muted())
        self._summary_text.setWordWrap(True)
        body.addWidget(self._summary_text)
        pills = QWidget()
        pills_layout = QHBoxLayout(pills)
        pills_layout.setContentsMargins(0, scaled_int(8, profile.grid_spacing_scale), 0, 0)
        self._pill_preview = Pill(translate(K.EXEC_CARD_PILL_PREVIEW), "green")
        self._pill_review = Pill(translate(K.EXEC_CARD_PILL_REVIEW), "yellow")
        pills_layout.addWidget(self._pill_preview)
        pills_layout.addWidget(self._pill_review)
        body.addWidget(pills)
        actions = QHBoxLayout()
        actions.setSpacing(actions_spacing)
        actions.setContentsMargins(0, scaled_int(16, profile.grid_spacing_scale), 0, 0)
        self._apply_btn = Button(translate(K.EXEC_CARD_BTN_MOVE), "primary")
        self._apply_btn.clicked.connect(self.move_files_clicked.emit)
        actions.addWidget(self._apply_btn)
        self._create_tree_btn = Button(translate(K.EXEC_CARD_BTN_TREE), "success")
        self._create_tree_btn.clicked.connect(self.create_folder_tree_clicked.emit)
        actions.addWidget(self._create_tree_btn)
        self._undo_btn = Button(translate(K.EXEC_CARD_BTN_UNDO), "danger")
        self._undo_btn.clicked.connect(self.rollback_clicked.emit)
        actions.addWidget(self._undo_btn)
        body.addLayout(actions)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._header.set_header_texts(
            translate(K.EXEC_CARD_HEADER_TITLE),
            translate(K.EXEC_CARD_HEADER_DESC),
        )
        self._status_pill.set_text_and_color(translate(K.EXEC_CARD_STATUS_READY), "green")
        self._summary_title.setText(translate(K.EXEC_CARD_SUMMARY_TITLE))
        self._summary_text.setText(translate(K.EXEC_CARD_SUMMARY_TEXT))
        self._pill_preview.setText(translate(K.EXEC_CARD_PILL_PREVIEW))
        self._pill_review.setText(translate(K.EXEC_CARD_PILL_REVIEW))
        self._apply_btn.setText(translate(K.EXEC_CARD_BTN_MOVE))
        self._create_tree_btn.setText(translate(K.EXEC_CARD_BTN_TREE))
        self._undo_btn.setText(translate(K.EXEC_CARD_BTN_UNDO))

    def set_status_pill(self, text: str, color: str) -> None:
        self._status_pill.set_text_and_color(text, color)
