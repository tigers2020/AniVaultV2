"""Pipeline table: QTableView + PipelineTableModel."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QTableView, QHeaderView
from PySide6.QtCore import Signal, QModelIndex

from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.models import PipelineTableModel, PipelineRow
from anivault.interfaces.gui import theme


class PipelineTable(QFrame):
    """Table with panel header. Selection feeds preview."""

    selection_changed = Signal(int)  # row index

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(
            PanelHeader(
                "Pipeline Result Table",
                "Parsed Filename Result, Parse Title Group, TMDB Korean Title Group 결과를 하나의 리스트 테이블로 통합",
                pill_text="Unified Table",
                pill_color="blue",
            )
        )
        self._model = PipelineTableModel()
        self._view = QTableView()
        self._view.setModel(self._model)
        self._view.setShowGrid(True)
        self._view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._view.verticalHeader().setVisible(False)
        self._view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._view.selectionModel().selectionChanged.connect(self._on_selection)
        layout.addWidget(self._view)
        self.setStyleSheet(theme.card_panel())

    def _on_selection(self) -> None:
        idx = self._view.currentIndex()
        if idx.isValid():
            self.selection_changed.emit(idx.row())

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._model.set_rows(rows)

    def model(self) -> PipelineTableModel:
        return self._model
