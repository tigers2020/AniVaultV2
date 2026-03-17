"""Execution card: Move summary + action row (Move Files, Undo, etc.)."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout, QLabel

from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.components.atoms import Button, Pill
from anivault.interfaces.gui import theme


class ExecutionCard(QFrame):
    """Execution panel: summary text, pills, action buttons."""

    apply_clicked = Signal()
    rollback_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Execution",
                "최종 이동 실행과 최근 작업 되돌리기를 같은 탭에서 관리",
                pill_text="Ready",
                pill_color="green",
            )
        )
        body = QVBoxLayout()
        body.setContentsMargins(18, 18, 18, 18)
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
        pills_layout.setContentsMargins(0, 8, 0, 0)
        pills_layout.addWidget(Pill("Preview Complete", "green"))
        pills_layout.addWidget(Pill("73 Review Files", "yellow"))
        body.addWidget(pills)
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.setContentsMargins(0, 16, 0, 0)
        apply_btn = Button("Move Files", "primary")
        apply_btn.clicked.connect(self.apply_clicked.emit)
        actions.addWidget(apply_btn)
        create_tree_btn = Button("Create Folder Tree Only", "success")
        create_tree_btn.clicked.connect(self.apply_clicked.emit)
        actions.addWidget(create_tree_btn)
        undo_btn = Button("Undo Last Move", "danger")
        undo_btn.clicked.connect(self.rollback_clicked.emit)
        actions.addWidget(undo_btn)
        layout.addLayout(body)
        self.setStyleSheet(theme.card_panel())
