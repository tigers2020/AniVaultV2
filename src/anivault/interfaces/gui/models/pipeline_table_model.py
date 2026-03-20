"""QAbstractTableModel for pipeline table. Row shape per plan §7.2."""

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, QPersistentModelIndex, Qt

from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow, PipelineRow

_INVALID_INDEX: QModelIndex = QModelIndex()

COLUMNS = [
    ("Original File", "original_file"),
    ("Parsed Title", "parsed_title"),
    ("Parse Title Group", "parse_group"),
    ("TMDB Korean Title Group", "tmdb_korean_title_group"),
    ("Year", "year"),
    ("Season", "season"),
    ("Res", "resolution"),
    ("Status", "status"),
]


class PipelineTableModel(QAbstractTableModel):
    """Model for pipeline table. One row per parsed-title group."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[PipelineGroupRow] = []

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        return len(COLUMNS)

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
        _, key = COLUMNS[index.column()]
        return getattr(row, key, "")

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        if 0 <= section < len(COLUMNS):
            return COLUMNS[section][0]
        return None

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rows(self) -> list[PipelineGroupRow]:
        """Return current group rows for sync to other views (list, tile, poster)."""
        return list(self._rows)

    def flat_rows(self) -> list[PipelineRow]:
        """All file-level rows in display order (groups, then members)."""
        out: list[PipelineRow] = []
        for g in self._rows:
            out.extend(g.members)
        return out

    def row_at(self, index: int) -> PipelineGroupRow | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None
