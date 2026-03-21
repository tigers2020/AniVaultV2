"""pipeline_proxy_model.py

파이프라인 테이블 정렬·필터용 QSortFilterProxyModel.

Author: Pom Kim
"""

from PySide6.QtCore import QSortFilterProxyModel, Qt


class PipelineProxyModel(QSortFilterProxyModel):
    """PipelineTableModel 위에 올려 정렬 등을 적용한다."""

    def __init__(self, parent=None):
        """대소문자 무시 정렬을 켠다.

        Args:
            self: 이 프록시.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
