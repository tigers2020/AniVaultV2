"""Operations page: FolderStructurePreview + ExecutionCard + LogList (organisms only)."""

from PySide6.QtWidgets import QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.organisms import (
    ExecutionCard,
    FolderStructurePreview,
    LogList,
)
from anivault.interfaces.gui.presenters import OperationsPresenter


class OperationsPage(QWidget):
    """Operations: folder structure list + execution card + log list (two-col)."""

    def __init__(self, parent=None, presenter: OperationsPresenter | None = None):
        super().__init__(parent)
        self._presenter = presenter if presenter is not None else OperationsPresenter(parent=self)
        if presenter is not None:
            self._presenter.setParent(self)
        exec_card = ExecutionCard()
        exec_card.apply_clicked.connect(self._presenter.on_apply_clicked)
        exec_card.rollback_clicked.connect(self._presenter.on_rollback_clicked)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.addWidget(FolderStructurePreview())
        two_col = QWidget()
        two_col_layout = QHBoxLayout(two_col)
        two_col_layout.setSpacing(18)
        two_col_layout.addWidget(exec_card, 12)
        two_col_layout.addWidget(LogList(), 8)
        content_layout.addWidget(two_col)
        scroll.setWidget(content)
        layout.addWidget(scroll)
