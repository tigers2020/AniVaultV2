"""pipeline_table_model.py

파이프라인 테이블용 QAbstractTableModel. 행은 파싱 제목 그룹 단위.

Author: Pom Kim
"""

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
    """그룹 행 리스트를 테이블 컬럼에 매핑한다."""

    def __init__(self, parent: QObject | None = None) -> None:
        """빈 그룹 목록으로 모델을 만든다.

        Args:
            self: 이 모델.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self._rows: list[PipelineGroupRow] = []

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        """루트일 때 그룹 개수를 반환한다.

        Args:
            self: 이 모델.
            parent: 부모 인덱스. 유효하면 0.

        Returns:
            행 수.
        """
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = _INVALID_INDEX) -> int:
        """컬럼 수는 COLUMNS 길이.

        Args:
            self: 이 모델.
            parent: 미사용.

        Returns:
            컬럼 수.
        """
        return len(COLUMNS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """DisplayRole일 때 셀 문자열을 반환한다.

        Args:
            self: 이 모델.
            index: 셀 인덱스.
            role: Qt ItemDataRole.

        Returns:
            표시 값 또는 None.
        """
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        row = self._rows[index.row()]
        _, key = COLUMNS[index.column()]
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
        """가로 헤더에 컬럼 타이틀을 반환한다.

        Args:
            self: 이 모델.
            section: 컬럼 인덱스.
            orientation: 가로/세로.
            role: Qt ItemDataRole.

        Returns:
            헤더 문자열 또는 None.
        """
        if orientation != Qt.Orientation.Horizontal or role != Qt.ItemDataRole.DisplayRole:
            return None
        if 0 <= section < len(COLUMNS):
            return COLUMNS[section][0]
        return None

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        """그룹 목록을 통째로 바꾸고 모델을 리셋한다.

        Args:
            self: 이 모델.
            rows: 새 그룹 행 목록.

        Returns:
            None.
        """
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rows(self) -> list[PipelineGroupRow]:
        """다른 뷰 동기화용 현재 그룹 행 복사본.

        Args:
            self: 이 모델.

        Returns:
            그룹 행 리스트.
        """
        return list(self._rows)

    def flat_rows(self) -> list[PipelineRow]:
        """표시 순서대로 모든 파일 행을 펼친다.

        Args:
            self: 이 모델.

        Returns:
            PipelineRow 리스트.
        """
        out: list[PipelineRow] = []
        for g in self._rows:
            out.extend(g.members)
        return out

    def row_at(self, index: int) -> PipelineGroupRow | None:
        """인덱스에 해당하는 그룹 행을 반환한다.

        Args:
            self: 이 모델.
            index: 0 기반 행 인덱스.

        Returns:
            그룹 행 또는 범위 밖이면 None.
        """
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None
