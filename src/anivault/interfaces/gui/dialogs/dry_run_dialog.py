"""dry_run_dialog.py

이동 계획 미리보기(소스·대상 목록)와 실제 적용 요청.

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

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button


class DryRunDialog(QDialog):
    """Dry Run 결과 테이블. 실제 이동 시 apply_requested 시그널."""

    apply_requested = Signal()

    def __init__(
        self,
        moves: list[tuple[str, str]],
        parent=None,
    ) -> None:
        """테이블과 버튼을 구성한다.

        Args:
            self: 이 대화상자.
            moves: (source_path, destination_path) 목록.
            parent: 부모 위젯.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("Dry Run — 이동 미리보기")
        self.setMinimumSize(900, 480)
        self.setStyleSheet(theme.card_panel())
        layout = QVBoxLayout(self)
        self._table = QTableWidget(len(moves), 2)
        self._table.setHorizontalHeaderLabels(["원본 경로", "대상 경로"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (src, dst) in enumerate(moves):
            self._table.setItem(row, 0, QTableWidgetItem(src))
            self._table.setItem(row, 1, QTableWidgetItem(dst))
        layout.addWidget(self._table)
        actions = QHBoxLayout()
        actions.addStretch(1)
        apply_btn = Button("실제 이동", "primary")
        apply_btn.clicked.connect(self._on_apply_clicked)
        close_btn = Button("닫기", "default")
        close_btn.clicked.connect(self.reject)
        actions.addWidget(apply_btn)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

    def _on_apply_clicked(self) -> None:
        """실제 이동을 요청한다. 완료 후 부모가 닫는다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        self.apply_requested.emit()
