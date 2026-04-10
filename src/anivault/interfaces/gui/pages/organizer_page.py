"""organizer_page.py

StatsGrid + PipelineResultPanel. 데이터는 OrganizerPresenter.

Author: Pom Kim
"""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from anivault.constants.gui.settings import (
    auto_scan_on_first_show_from_loaded,
    scan_source_path_from_loaded,
)
from anivault.contracts.pipeline import PipelineRow
from anivault.interfaces.gui.components.organisms import FolderScanBar, StatsGrid
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.presenters import OrganizerPresenter
from anivault.interfaces.gui.settings_storage import load_all, save_all
from anivault.interfaces.gui.templates import PipelineResultPanel


class OrganizerPage(QWidget):
    """통계·스캔 바·파이프라인 결과 패널."""

    def __init__(
        self,
        parent=None,
        model: PipelineTableModel | None = None,
        presenter: OrganizerPresenter | None = None,
    ):
        """모델·Presenter·패널을 연결한다.

        Args:
            self: 이 위젯.
            parent: 부모 위젯(선택).
            model: 파이프라인 테이블 모델.
            presenter: OrganizerPresenter. None이면 자체 생성.

        Returns:
            None.
        """
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
        source_path = scan_source_path_from_loaded(load_all())
        self._scan_bar.set_path(source_path)
        self._scan_bar.scan_clicked.connect(self._presenter.on_scan_clicked)
        self._scan_bar.match_clicked.connect(self._presenter.on_match_clicked)
        self._scan_bar.dry_run_clicked.connect(self._presenter.on_dry_run_clicked)
        self._scan_bar.path_changed.connect(self._on_scan_path_changed)
        self._presenter.set_dry_run_enabled_handler(self._scan_bar.set_dry_run_enabled)
        self._presenter.set_pipeline_busy_handler(self._scan_bar.set_pipeline_busy)
        self._presenter.set_pipeline_result_panel(self._result_panel)
        self._presenter.refresh_pipeline_action_bar_state()
        self._result_panel.manual_match_requested.connect(
            self._presenter.on_manual_tmdb_match_clicked
        )
        content_layout.addWidget(self._scan_bar)
        self._stats_grid = StatsGrid()
        content_layout.addWidget(self._stats_grid)
        content_layout.addWidget(self._result_panel)
        # Make Pipeline Result panel consume remaining vertical space.
        content_layout.setStretchFactor(self._result_panel, 1)
        self._model.modelReset.connect(self._update_stats)
        # Chunked parse uses append_row_groups (rowsInserted); TMDB incremental uses dataChanged.
        self._model.rowsInserted.connect(self._update_stats)
        self._model.rowsRemoved.connect(self._update_stats)
        self._model.dataChanged.connect(self._update_stats)
        self._update_stats()
        layout.addLayout(content_layout, 1)

    def _on_scan_path_changed(self, path: str) -> None:
        """Organizer 스캔 경로 변경 시 설정에 저장한다.

        Args:
            self: 이 위젯.
            path: 새 소스 경로.

        Returns:
            None.
        """
        save_all({"scan_build": {"source_path": path or ""}})

    def _update_stats(self) -> None:
        """모델에서 스캔·파싱·TMDB·계획 수를 집계해 StatsGrid에 넘긴다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        rows: list[PipelineRow] = self._model.flat_rows()
        scanned = len(rows)
        parsed = sum(1 for r in rows if (r.parsed_title or "").strip())
        tmdb_matches = sum(1 for r in rows if (r.tmdb_korean_title_group or "").strip())
        groups = self._model.rowCount()
        self._stats_grid.set_stats(
            scanned=scanned,
            parsed=parsed,
            tmdb_matches=tmdb_matches,
            groups=groups,
        )

    def showEvent(self, event: QShowEvent) -> None:
        """설정에서 경로를 다시 읽고, 최초 한 번 자동 스캔을 예약한다.

        Args:
            self: 이 위젯.
            event: 표시 이벤트.

        Returns:
            None.
        """
        super().showEvent(event)
        settings = load_all()
        source_path = scan_source_path_from_loaded(settings)
        self._scan_bar.set_path(source_path)
        auto_scan = auto_scan_on_first_show_from_loaded(settings)
        if source_path and not self._auto_scan_done and auto_scan:
            self._auto_scan_done = True
            QTimer.singleShot(100, lambda: self._presenter.on_scan_clicked(source_path))
