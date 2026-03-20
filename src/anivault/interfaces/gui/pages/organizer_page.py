"""Organizer page: StatsGrid + PipelineResultPanel (organisms + templates)."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from anivault.interfaces.gui.components.organisms import FolderScanBar, StatsGrid
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel
from anivault.interfaces.gui.presenters import OrganizerPresenter
from anivault.interfaces.gui.settings_storage import load_all, save_all
from anivault.interfaces.gui.templates import PipelineResultPanel


class OrganizerPage(QWidget):
    """Organizer: stats + pipeline table + poster grid. Data via OrganizerPresenter."""

    def __init__(
        self,
        parent=None,
        model: PipelineTableModel | None = None,
        presenter: OrganizerPresenter | None = None,
    ):
        super().__init__(parent)
        self._auto_scan_done = False
        self._model = model if model is not None else PipelineTableModel()
        self._presenter = (
            presenter
            if presenter is not None
            else OrganizerPresenter(pipeline_model=self._model, parent=self)
        )
        if presenter is not None:
            self._presenter.setParent(self)
        self._result_panel = PipelineResultPanel(model=self._model)
        self._result_panel.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        content_layout = QVBoxLayout()
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        self._scan_bar = FolderScanBar()
        source_path = load_all().get("scan_build", {}).get("source_path", "") or ""
        self._scan_bar.set_path(source_path)
        self._scan_bar.scan_clicked.connect(self._presenter.on_scan_clicked)
        self._scan_bar.path_changed.connect(self._on_scan_path_changed)
        content_layout.addWidget(self._scan_bar)
        self._stats_grid = StatsGrid()
        content_layout.addWidget(self._stats_grid)
        content_layout.addWidget(self._result_panel)
        # Make Pipeline Result panel consume remaining vertical space.
        content_layout.setStretchFactor(self._result_panel, 1)
        self._model.modelReset.connect(self._update_stats)
        self._update_stats()
        layout.addLayout(content_layout, 1)

    def _on_scan_path_changed(self, path: str) -> None:
        """Persist source_path to settings when user changes Organizer scan path."""
        save_all({"scan_build": {"source_path": path or ""}})

    def _update_stats(self) -> None:
        """Refresh stats grid from pipeline model (scanned, parsed, tmdb, planned)."""
        rows: list[PipelineRow] = self._model.flat_rows()
        scanned = len(rows)
        parsed = sum(1 for r in rows if (r.parsed_title or "").strip())
        tmdb_matches = sum(1 for r in rows if (r.tmdb_korean_title_group or "").strip())
        planned = sum(1 for r in rows if (r.target_path or "").strip())
        self._stats_grid.set_stats(
            scanned=scanned,
            parsed=parsed,
            tmdb_matches=tmdb_matches,
            planned=planned,
        )

    def showEvent(self, event: QShowEvent) -> None:
        """Reload source_path from settings; auto-scan once with delay so UI is ready."""
        super().showEvent(event)
        source_path = load_all().get("scan_build", {}).get("source_path", "") or ""
        self._scan_bar.set_path(source_path)
        if source_path and not self._auto_scan_done:
            self._auto_scan_done = True
            QTimer.singleShot(100, lambda: self._presenter.on_scan_clicked(source_path))
