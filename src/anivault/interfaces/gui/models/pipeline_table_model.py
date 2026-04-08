"""pipeline_table_model.py

파이프라인 테이블용 QAbstractTableModel. 행은 파일 그룹 단위.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, QPersistentModelIndex, Qt

from anivault.constants.gui.tables import PIPELINE_TABLE_COLUMNS
from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow, PipelineRow

_INVALID_INDEX: QModelIndex = QModelIndex()


class PipelineTableModel(QAbstractTableModel):
    """그룹 리스트를 테이블 컬럼에 매핑한다."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[PipelineGroupRow] = []

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        return len(PIPELINE_TABLE_COLUMNS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        row = self._rows[index.row()]
        _, key = PIPELINE_TABLE_COLUMNS[index.column()]
        value = getattr(row, key, "")
        if key == "season":
            s = (value or "").strip()
            return s if s else "1"
        return value

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        if 0 <= section < len(PIPELINE_TABLE_COLUMNS):
            return PIPELINE_TABLE_COLUMNS[section][0]
        return None

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def clear_with_reset(self) -> None:
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def append_row_groups(self, rows: list[PipelineGroupRow]) -> None:
        if not rows:
            return
        start = len(self._rows)
        end = start + len(rows) - 1
        self.beginInsertRows(_INVALID_INDEX, start, end)
        self._rows.extend(rows)
        self.endInsertRows()

    def update_rows_if_compatible(self, rows: list[PipelineGroupRow]) -> bool:
        if len(rows) != len(self._rows):
            return False
        for old_g, new_g in zip(self._rows, rows, strict=True):
            if len(old_g.members) != len(new_g.members):
                return False
            old_paths = [m.original_file for m in old_g.members]
            new_paths = [m.original_file for m in new_g.members]
            if old_paths != new_paths:
                return False

        self._rows = list(rows)
        if not self._rows:
            return True
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._rows) - 1, len(PIPELINE_TABLE_COLUMNS) - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
        return True

    def rows(self) -> list[PipelineGroupRow]:
        return list(self._rows)

    def flat_rows(self) -> list[PipelineRow]:
        out: list[PipelineRow] = []
        for g in self._rows:
            out.extend(g.members)
        return out

    def row_at(self, index: int) -> PipelineGroupRow | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None
