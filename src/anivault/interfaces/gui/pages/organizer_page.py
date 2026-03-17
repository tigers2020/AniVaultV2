"""Organizer page: StatsGrid + PipelineResultPanel (organisms only)."""

from PySide6.QtWidgets import QScrollArea, QVBoxLayout, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.organisms import (
    FolderScanBar,
    PipelineResultPanel,
    StatsGrid,
)
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.presenters import OrganizerPresenter


class OrganizerPage(QWidget):
    """Organizer: stats + pipeline table + poster grid. Data via OrganizerPresenter."""

    def __init__(
        self,
        parent=None,
        model: PipelineTableModel | None = None,
        presenter: OrganizerPresenter | None = None,
    ):
        super().__init__(parent)
        self._model = model if model is not None else PipelineTableModel()
        self._presenter = presenter if presenter is not None else OrganizerPresenter(
            pipeline_model=self._model, parent=self
        )
        if presenter is not None:
            self._presenter.setParent(self)
        panel = PipelineResultPanel(model=self._model)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        content = QWidget()
        content_layout = QVBoxLayout(content)
        self._scan_bar = FolderScanBar()
        self._scan_bar.scan_clicked.connect(self._presenter.on_scan_clicked)
        content_layout.addWidget(self._scan_bar)
        content_layout.addWidget(StatsGrid())
        content_layout.addWidget(panel)
        scroll.setWidget(content)
        layout.addWidget(scroll)
