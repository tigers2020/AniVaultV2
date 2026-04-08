"""dry_run_dialog.py

이동 계획 미리보기와 실제 적용 요청 dialog.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from anivault.constants.gui.components import (
    DRY_RUN_DIALOG_BUTTON_APPLY,
    DRY_RUN_DIALOG_BUTTON_CLOSE,
    DRY_RUN_DIALOG_HEADER_DESTINATION,
    DRY_RUN_DIALOG_HEADER_SOURCE,
    DRY_RUN_DIALOG_TITLE,
)
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button


class DryRunDialog(QDialog):
    """Dry Run 결과 테이블과 실제 이동 버튼 dialog."""

    apply_requested = Signal()

    def __init__(self, moves: list[tuple[str, str]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(DRY_RUN_DIALOG_TITLE)
        self.setMinimumSize(900, 480)
        self.setStyleSheet(theme.card_panel())
        layout = QVBoxLayout(self)
        self._table = QTableWidget(len(moves), 2)
        self._table.setHorizontalHeaderLabels(
            [DRY_RUN_DIALOG_HEADER_SOURCE, DRY_RUN_DIALOG_HEADER_DESTINATION]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (src, dst) in enumerate(moves):
            self._table.setItem(row, 0, QTableWidgetItem(src))
            self._table.setItem(row, 1, QTableWidgetItem(dst))
        layout.addWidget(self._table)
        actions = QHBoxLayout()
        actions.addStretch(1)
        apply_btn = Button(DRY_RUN_DIALOG_BUTTON_APPLY, "primary")
        apply_btn.clicked.connect(self._on_apply_clicked)
        close_btn = Button(DRY_RUN_DIALOG_BUTTON_CLOSE, "default")
        close_btn.clicked.connect(self.reject)
        actions.addWidget(apply_btn)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

    def _on_apply_clicked(self) -> None:
        self.apply_requested.emit()
