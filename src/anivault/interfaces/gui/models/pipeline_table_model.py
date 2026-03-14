"""QAbstractTableModel for pipeline table. Row shape per plan §7.2."""

from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass
class PipelineRow:
    """One row in pipeline table. Shared by table / poster / operations."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    target_path: str


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
    """Model for pipeline table. Edit not required for now."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[PipelineRow] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
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

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_at(self, index: int) -> PipelineRow | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None
