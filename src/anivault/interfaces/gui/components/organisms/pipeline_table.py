"""pipeline_table.py

QTableView와 PipelineTableModel을 묶은 파이프라인 결과 테이블 organism.

Author: Pom Kim
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHeaderView, QTableView, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import PanelHeader
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineTableModel


class PipelineTable(QFrame):
    """선택 가능한 파이프라인 테이블. 헤더 패널은 옵션."""

    selection_changed = Signal(int)  # row index

    def __init__(
        self,
        show_header: bool = True,
        model: PipelineTableModel | None = None,
        parent=None,
    ):
        """테이블 뷰·모델·선택 시그널을 구성한다.

        Args:
            self: 이 테이블 위젯.
            show_header: 상단 PanelHeader 표시 여부.
            model: 외부 모델. None이면 내부 생성.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if show_header:
            layout.addWidget(
                PanelHeader(
                    "Pipeline Result Table",
                    "Parsed Filename Result, Parse Title Group, TMDB Korean Title Group 결과를 하나의 리스트 테이블로 통합",
                    pill_text="Unified Table",
                    pill_color="blue",
                )
            )
        self._model = model if model is not None else PipelineTableModel()
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
        """현재 행 선택이 바뀌면 selection_changed에 행 인덱스를 emit한다.

        Args:
            self: 이 테이블 위젯.

        Returns:
            None.
        """
        idx = self._view.currentIndex()
        if idx.isValid():
            self.selection_changed.emit(idx.row())

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        """모델에 그룹 행 목록을 설정한다.

        Args:
            self: 이 테이블 위젯.
            rows: 파이프라인 그룹 행.

        Returns:
            None.
        """
        self._model.set_rows(rows)

    def model(self) -> PipelineTableModel:
        """내부 PipelineTableModel을 반환한다.

        Args:
            self: 이 테이블 위젯.

        Returns:
            테이블 모델 인스턴스.
        """
        return self._model

    def select_row(self, row: int) -> None:
        """지정 행을 선택한다. 범위 밖이면 선택을 해제한다.

        Args:
            self: 이 테이블 위젯.
            row: 행 인덱스.

        Returns:
            None.
        """
        n = self._model.rowCount()
        if row < 0 or row >= n:
            self._view.clearSelection()
            return
        self._view.selectRow(row)
