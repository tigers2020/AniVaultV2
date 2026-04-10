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

from anivault.application.ports.poster_sync_port import PosterAssetSyncPort
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.contracts.parse import ParseInput, ParseResult
from anivault.contracts.pipeline import MatchInput, MatchResult, PipelineRow
from anivault.contracts.planning import ApplyInput, ApplyResult, PlanInput, PlanResult
from anivault.contracts.progress import ProgressEvent
from anivault.contracts.scan import ScanInput, ScanResult
from anivault.contracts.tmdb import TmdbSearchInput, TmdbSeriesCandidate
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import PipelineTableModel, group_pipeline_rows
from anivault.interfaces.gui.presenters.organizing.match_coordinator import MatchCoordinator
from anivault.interfaces.gui.presenters.organizing.plan_apply_coordinator import (
    PlanApplyCoordinator,
)
from anivault.interfaces.gui.presenters.organizing.scan_parse_coordinator import (
    ScanParseCoordinator,
)
from anivault.interfaces.gui.presenters.row_mapper import match_file_to_pipeline_row
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
ScanExecuteFn = Callable[[ScanInput, Callable[[ProgressEvent], None] | None, Event], ScanResult]
ParseExecuteFn = Callable[
    [ParseInput, Callable[[ProgressEvent], None] | None, Event],
    ParseResult,
]
CachedTmdbHydrateFn = Callable[[MatchInput], MatchResult]
CachedTmdbMissingFillFn = Callable[[MatchInput, object, Event], MatchResult]


@dataclass(frozen=True, slots=True)
class OrganizerPresenterPorts:
    """TMDB/포스터 연동에 필요한 저장소 포트 묶음."""

    title_match: TitleMatchRepository | None = None
    title_groups: TitleGroupRepository | None = None
    poster_sync: PosterAssetSyncPort | None = None


@dataclass(frozen=True, slots=True)
class OrganizerPresenterUseCases:
    """OrganizerPresenter가 호출하는 유즈케이스 함수 묶음."""

    scan_execute: ScanExecuteFn | None = None
    parse_execute: ParseExecuteFn | None = None
    match_execute: (
        Callable[
            [MatchInput, Callable[[ProgressEvent], None] | None, Event],
            MatchResult,
        ]
        | None
    ) = None
    tmdb_search_execute: (
        Callable[
            [TmdbSearchInput, Callable[[ProgressEvent], None] | None, Event],
            tuple[TmdbSeriesCandidate, ...],
        ]
        | None
    ) = None
    plan_execute: PlanExecuteFn | None = None
    apply_execute: ApplyExecuteFn | None = None
    sync_title_groups_execute: Callable[[int], None] | None = None
    cached_tmdb_hydrate_execute: CachedTmdbHydrateFn | None = None
    cached_tmdb_missing_fill_execute: CachedTmdbMissingFillFn | None = None


class OrganizerPresenter(QObject):
    """Organizer 페이지의 공용 상태, worker 추적, coordinator 위임."""

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        use_cases: OrganizerPresenterUseCases | None = None,
        progress_dialog: ProgressDialog | None = None,
        include_companion_subtitles: bool = True,
        exclude_subtitles_with_paired_video: bool = False,
        ports: OrganizerPresenterPorts | None = None,
        parent: QObject | None = None,
        **legacy_use_cases: Any,
    ) -> None:
        super().__init__(parent)
        resolved_use_cases = self._resolve_use_cases(
            use_cases=use_cases,
            legacy_use_cases=legacy_use_cases,
        )
        self._model = pipeline_model
        self._include_companion_subtitles = include_companion_subtitles
        self._exclude_subtitles_with_paired_video = exclude_subtitles_with_paired_video
        self._scan_execute = resolved_use_cases.scan_execute
        self._parse_execute = resolved_use_cases.parse_execute
        self._match_execute = resolved_use_cases.match_execute
        self._tmdb_search_execute = resolved_use_cases.tmdb_search_execute
        self._plan_execute = resolved_use_cases.plan_execute
        self._apply_execute = resolved_use_cases.apply_execute
        self._progress_dialog = progress_dialog
        self._sync_title_groups_execute = resolved_use_cases.sync_title_groups_execute
        self._cached_tmdb_hydrate_execute = resolved_use_cases.cached_tmdb_hydrate_execute
        self._cached_tmdb_missing_fill_execute = resolved_use_cases.cached_tmdb_missing_fill_execute
        _ports = ports or OrganizerPresenterPorts()
        self._title_match = _ports.title_match
        self._title_groups = _ports.title_groups
        self._poster_sync = _ports.poster_sync
        self._parse_index_root_id: int | None = None
        self._current_library_root_id: int | None = None
        self._worker_thread: QThread | None = None
        self._worker_threads: list[QThread] = []
        self._dry_run_enabled_handler: Callable[[bool], None] | None = None
        self._pipeline_busy_handler: Callable[[bool], None] | None = None
        self._pending_plan: PlanResult | None = None
        self._scan_progress_handoff_done: bool = False
        self._pipeline_panel: PipelineResultPanel | None = None
        self._tmdb_worker_keepalive: UseCaseWorker | None = None

        self._scan_parse_coordinator = ScanParseCoordinator(self)
        self._match_coordinator = MatchCoordinator(self)
        self._plan_apply_coordinator = PlanApplyCoordinator(self)

    @staticmethod
    def _resolve_use_cases(
        *,
        use_cases: OrganizerPresenterUseCases | None,
        legacy_use_cases: dict[str, Any],
    ) -> OrganizerPresenterUseCases:
        if use_cases is not None and legacy_use_cases:
            raise TypeError("use_cases and legacy use-case kwargs cannot be mixed.")
        if use_cases is not None:
            return use_cases
        if not legacy_use_cases:
            return OrganizerPresenterUseCases()
        allowed_keys = {
            "scan_execute",
            "parse_execute",
            "match_execute",
            "tmdb_search_execute",
            "plan_execute",
            "apply_execute",
            "sync_title_groups_execute",
            "cached_tmdb_hydrate_execute",
            "cached_tmdb_missing_fill_execute",
        }
        unknown_keys = sorted(set(legacy_use_cases) - allowed_keys)
        if unknown_keys:
            raise TypeError(f"Unexpected OrganizerPresenter kwargs: {', '.join(unknown_keys)}")
        return OrganizerPresenterUseCases(**legacy_use_cases)

    def set_pipeline_result_panel(self, panel: PipelineResultPanel | None) -> None:
        self._pipeline_panel = panel

    def model(self) -> PipelineTableModel:
        return self._model

    def progress_dialog(self) -> ProgressDialog | None:
        return self._progress_dialog

    def scan_execute(self) -> ScanExecuteFn | None:
        return self._scan_execute

    def parse_execute(self) -> ParseExecuteFn | None:
        return self._parse_execute

    def match_execute(
        self,
    ) -> Callable[[MatchInput, Callable[[ProgressEvent], None] | None, Event], MatchResult] | None:
        return self._match_execute

    def tmdb_search_execute(
        self,
    ) -> (
        Callable[
            [TmdbSearchInput, Callable[[ProgressEvent], None] | None, Event],
            tuple[TmdbSeriesCandidate, ...],
        ]
        | None
    ):
        return self._tmdb_search_execute

    def plan_execute(self) -> PlanExecuteFn | None:
        return self._plan_execute

    def apply_execute(self) -> ApplyExecuteFn | None:
        return self._apply_execute

    def sync_title_groups_execute(self) -> Callable[[int], None] | None:
        return self._sync_title_groups_execute

    def cached_tmdb_hydrate_execute(self) -> CachedTmdbHydrateFn | None:
        return self._cached_tmdb_hydrate_execute

    def cached_tmdb_missing_fill_execute(self) -> CachedTmdbMissingFillFn | None:
        return self._cached_tmdb_missing_fill_execute

    def title_match_repository(self) -> TitleMatchRepository | None:
        return self._title_match

    def title_group_repository(self) -> TitleGroupRepository | None:
        return self._title_groups

    def poster_sync_port(self) -> PosterAssetSyncPort | None:
        return self._poster_sync

    def include_companion_subtitles(self) -> bool:
        return self._include_companion_subtitles

    def exclude_subtitles_with_paired_video(self) -> bool:
        return self._exclude_subtitles_with_paired_video

    def current_library_root_id(self) -> int | None:
        return self._current_library_root_id

    def set_current_library_root_id(self, value: int | None) -> None:
        self._current_library_root_id = value

    def parse_index_root_id(self) -> int | None:
        return self._parse_index_root_id

    def set_parse_index_root_id(self, value: int | None) -> None:
        self._parse_index_root_id = value

    def scan_progress_handoff_done(self) -> bool:
        return self._scan_progress_handoff_done

    def set_scan_progress_handoff_done(self, value: bool) -> None:
        self._scan_progress_handoff_done = value

    def pipeline_panel(self) -> PipelineResultPanel | None:
        return self._pipeline_panel

    def pending_plan(self) -> PlanResult | None:
        return self._pending_plan

    def set_pending_plan(self, value: PlanResult | None) -> None:
        self._pending_plan = value

    def set_tmdb_worker_keepalive(self, worker: UseCaseWorker | None) -> None:
        self._tmdb_worker_keepalive = worker

    def set_current_worker_thread(self, thread: QThread | None) -> None:
        self._worker_thread = thread

    def _finish_worker_session(self, dialog: ProgressDialog, hide: bool) -> None:
        dialog.mark_work_finished()
        if hide:
            dialog.hide_progress()

    def finish_worker_session(self, dialog: ProgressDialog, *, hide: bool) -> None:
        self._finish_worker_session(dialog, hide)

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

    def has_active_pipeline_work(self) -> bool:
        for t in self._worker_threads:
            is_running = getattr(t, "isRunning", None)
            if callable(is_running) and is_running():
                return True
        return False

    def set_pipeline_busy_handler(self, handler: Callable[[bool], None] | None) -> None:
        self._pipeline_busy_handler = handler

    def refresh_pipeline_action_bar_state(self) -> None:
        busy = self.has_active_pipeline_work()
        if self._pipeline_busy_handler is not None:
            self._pipeline_busy_handler(busy)
        dry = self._dry_run_should_enable() and not busy
        if self._dry_run_enabled_handler is not None:
            self._dry_run_enabled_handler(dry)

    def run_scan_after_apply_completion(self, path: str) -> None:
        self._scan_parse_coordinator.run_scan_after_apply_completion(path)

    def register_worker_thread(self, thread: QThread) -> None:
        self._worker_thread = thread
        if thread not in self._worker_threads:
            self._worker_threads.append(thread)
            thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self.refresh_pipeline_action_bar_state()

    def _on_scan_error(self, exc: Exception) -> None:
        del exc
        self._current_library_root_id = None
        self._parse_index_root_id = None
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()

    def on_scan_error(self, exc: Exception) -> None:
        self._on_scan_error(exc)

    def _on_worker_finished(self, thread: QThread) -> None:
        if thread in self._worker_threads:
            self._worker_threads.remove(thread)
        if self._worker_thread is thread:
            self._worker_thread = self._worker_threads[-1] if self._worker_threads else None
        self.refresh_pipeline_action_bar_state()

    def on_worker_finished(self, thread: QThread) -> None:
        self._on_worker_finished(thread)

    def _match_file_to_pipeline_row(self, match_file: PipelineRow) -> PipelineRow:
        return self.match_file_to_pipeline_row(match_file)

    def match_file_to_pipeline_row(self, match_file: PipelineRow) -> PipelineRow:
        return match_file_to_pipeline_row(match_file, title_match=self._title_match)

    def _parent_widget(self) -> QWidget | None:
        parent = self.parent()
        return parent if isinstance(parent, QWidget) else None

    def parent_widget(self) -> QWidget | None:
        return self._parent_widget()

    def set_dry_run_enabled_handler(self, handler: Callable[[bool], None] | None) -> None:
        self._dry_run_enabled_handler = handler

    def _notify_dry_run(self, enabled: bool) -> None:
        """호환용: Dry Run 외 스캔/매칭 버튼까지 `refresh_pipeline_action_bar_state`로 맞춘다."""

        del enabled
        self.refresh_pipeline_action_bar_state()

    def notify_dry_run(self, enabled: bool) -> None:
        self._notify_dry_run(enabled)

    def _dry_run_should_enable(self) -> bool:
        from anivault.interfaces.gui.models import pipeline_rows_ready_for_plan

        return bool(pipeline_rows_ready_for_plan(self._model.flat_rows()))

    def dry_run_should_enable(self) -> bool:
        return self._dry_run_should_enable()

    def set_rows(self, rows: list[PipelineRow]) -> None:
        self._model.set_rows(group_pipeline_rows(rows))
