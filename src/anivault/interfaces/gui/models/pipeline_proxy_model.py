"""QSortFilterProxyModel for pipeline table. Sort/filter by column."""

from PySide6.QtCore import QSortFilterProxyModel, Qt


class PipelineProxyModel(QSortFilterProxyModel):
    """Proxy over PipelineTableModel for sorting and filtering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
