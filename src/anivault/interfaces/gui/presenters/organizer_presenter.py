"""organizer_presenter.py

Organizer 페이지의 공용 상태와 coordinator 위임 지점.

Author: Pom Kim
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from typing import Any

from PySide6.QtCore import QObject, QThread
from PySide6.QtWidgets import QWidget

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.parse import ParseInput, ParseResult
from anivault.application.dto.plan import ApplyInput, ApplyResult, PlanInput, PlanResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.poster_sync_port import PosterAssetSyncPort
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel, group_pipeline_rows
from anivault.interfaces.gui.presenters.organizing.match_coordinator import MatchCoordinator
from anivault.interfaces.gui.presenters.organizing.plan_apply_coordinator import (
    PlanApplyCoordinator,
)
from anivault.interfaces.gui.presenters.organizing.scan_parse_coordinator import (
    ScanParseCoordinator,
)
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker

logger = logging.getLogger(__name__)

PlanExecuteFn = Callable[
    [PlanInput, Callable[[ProgressEvent], None] | None, Event],
    PlanResult,
]
ApplyExecuteFn = Callable[
    [ApplyInput, Callable[[ProgressEvent], None] | None, Event],
    ApplyResult,
]
CachedTmdbHydrateFn = Callable[[MatchInput], MatchResult]
CachedTmdbMissingFillFn = Callable[[MatchInput, object, Event], MatchResult]


@dataclass(frozen=True, slots=True)
class OrganizerPresenterPorts:
    """TMDB/포스터 연동에 필요한 저장소 포트 묶음."""

    title_match: TitleMatchRepository | None = None
    title_groups: TitleGroupRepository | None = None
    poster_sync: PosterAssetSyncPort | None = None


class OrganizerPresenter(QObject):
    """Organizer 페이지의 공용 상태, worker 추적, coordinator 위임."""

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        scan_execute: Callable[[ScanInput, object, Any], ScanResult] | None = None,
        parse_execute: Callable[[ParseInput, object, Any], ParseResult] | None = None,
        match_execute: (
            Callable[
                [MatchInput, Callable[[ProgressEvent], None] | None, Event],
                MatchResult,
            ]
            | None
        ) = None,
        tmdb_search_execute: (
            Callable[
                [TmdbSearchInput, Callable[[ProgressEvent], None] | None, Event],
                tuple[TmdbSeriesCandidateDTO, ...],
            ]
            | None
        ) = None,
        plan_execute: PlanExecuteFn | None = None,
        apply_execute: ApplyExecuteFn | None = None,
        progress_dialog: ProgressDialog | None = None,
        include_companion_subtitles: bool = True,
        exclude_subtitles_with_paired_video: bool = False,
        sync_title_groups_execute: Callable[[int], None] | None = None,
        cached_tmdb_hydrate_execute: CachedTmdbHydrateFn | None = None,
        cached_tmdb_missing_fill_execute: CachedTmdbMissingFillFn | None = None,
        ports: OrganizerPresenterPorts | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = pipeline_model
        self._include_companion_subtitles = include_companion_subtitles
        self._exclude_subtitles_with_paired_video = exclude_subtitles_with_paired_video
        self._scan_execute = scan_execute
        self._parse_execute = parse_execute
        self._match_execute = match_execute
        self._tmdb_search_execute = tmdb_search_execute
        self._plan_execute = plan_execute
        self._apply_execute = apply_execute
        self._progress_dialog = progress_dialog
        self._sync_title_groups_execute = sync_title_groups_execute
        self._cached_tmdb_hydrate_execute = cached_tmdb_hydrate_execute
        self._cached_tmdb_missing_fill_execute = cached_tmdb_missing_fill_execute
        _ports = ports or OrganizerPresenterPorts()
        self._title_match = _ports.title_match
        self._title_groups = _ports.title_groups
        self._poster_sync = _ports.poster_sync
        self._parse_index_root_id: int | None = None
        self._current_library_root_id: int | None = None
        self._worker_thread: QThread | None = None
        self._worker_threads: list[QThread] = []
        self._dry_run_enabled_handler: Callable[[bool], None] | None = None
        self._pending_plan: PlanResult | None = None
        self._scan_progress_handoff_done: bool = False
        self._pipeline_panel: PipelineResultPanel | None = None
        self._tmdb_worker_keepalive: UseCaseWorker | None = None

        self._scan_parse_coordinator = ScanParseCoordinator(self)
        self._match_coordinator = MatchCoordinator(self)
        self._plan_apply_coordinator = PlanApplyCoordinator(self)

    def set_pipeline_result_panel(self, panel: PipelineResultPanel | None) -> None:
        self._pipeline_panel = panel

    def _finish_worker_session(self, dialog: ProgressDialog, hide: bool) -> None:
        dialog.mark_work_finished()
        if hide:
            dialog.hide_progress()

    def _disconnect_cancel_on_thread_finished(
        self,
        dialog: ProgressDialog,
        cancel_slot: Callable[[], None],
        thread: QThread,
    ) -> None:
        """Disconnect the shared cancel signal when a worker thread finishes."""

        def _disconnect_cancel() -> None:
            try:
                dialog.canceled.disconnect(cancel_slot)
            except (RuntimeError, TypeError, SystemError):
                logger.debug("Progress dialog cancel signal was already disconnected.")

        thread.finished.connect(_disconnect_cancel)

    def on_scan_clicked(self, path: str) -> None:
        self._scan_parse_coordinator.on_scan_clicked(path)

    def on_match_clicked(self) -> None:
        self._match_coordinator.on_match_clicked()

    def on_manual_tmdb_match_clicked(self) -> None:
        self._match_coordinator.on_manual_tmdb_match_clicked()

    def on_dry_run_clicked(self) -> None:
        self._plan_apply_coordinator.on_dry_run_clicked()

    def register_worker_thread(self, thread: QThread) -> None:
        self._worker_thread = thread
        if thread not in self._worker_threads:
            self._worker_threads.append(thread)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))

    def _on_scan_error(self, exc: Exception) -> None:
        del exc
        self._current_library_root_id = None
        self._parse_index_root_id = None
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()

    def _on_worker_finished(self, thread: QThread) -> None:
        if thread in self._worker_threads:
            self._worker_threads.remove(thread)
        if self._worker_thread is thread:
            self._worker_thread = self._worker_threads[-1] if self._worker_threads else None

    def _match_file_to_pipeline_row(self, match_file: MatchFileRow) -> PipelineRow:
        local_poster: str | None = None
        if self._title_match is not None:
            tmdb_series_id = (match_file.tmdb_series_id or "").strip()
            remote_poster_path = normalize_tmdb_remote_image_path(match_file.tmdb_poster_path)
            if tmdb_series_id and remote_poster_path:
                try:
                    local_poster = self._title_match.get_poster_local_path(
                        int(tmdb_series_id),
                        "poster",
                        remote_poster_path,
                    )
                except (OSError, TypeError, ValueError):
                    local_poster = None
        poster_display = resolve_final_poster_display_source(local_poster, match_file.poster_url)
        return PipelineRow(
            original_file=match_file.original_file,
            parsed_title=match_file.parsed_title,
            parse_group=match_file.parse_group,
            tmdb_korean_title_group=match_file.tmdb_korean_title_group,
            tmdb_series_id=match_file.tmdb_series_id,
            tmdb_poster_path=match_file.tmdb_poster_path,
            tmdb_backdrop_path=match_file.tmdb_backdrop_path,
            year=match_file.year,
            season=match_file.season,
            resolution=match_file.resolution,
            status=match_file.status,
            poster_url=poster_display,
            backdrop_url=match_file.backdrop_url,
            target_path=match_file.target_path,
            episode=match_file.episode,
        )

    def _parent_widget(self) -> QWidget | None:
        parent = self.parent()
        return parent if isinstance(parent, QWidget) else None

    def set_dry_run_enabled_handler(self, handler: Callable[[bool], None] | None) -> None:
        self._dry_run_enabled_handler = handler

    def _notify_dry_run(self, enabled: bool) -> None:
        if self._dry_run_enabled_handler is not None:
            self._dry_run_enabled_handler(enabled)

    def _dry_run_should_enable(self) -> bool:
        from anivault.interfaces.gui.models import pipeline_rows_ready_for_plan

        return bool(pipeline_rows_ready_for_plan(self._model.flat_rows()))

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._model.set_rows(group_pipeline_rows(rows))
