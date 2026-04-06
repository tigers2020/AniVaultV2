"""organizer_presenter.py

Organizer 페이지에서 스캔·파싱·TMDB 매칭 워커를 조율하고 파이프라인 모델을 갱신한다.

Author: Pom Kim
"""

import logging
from collections.abc import Callable
from threading import Event
from typing import Any

from PySide6.QtCore import QObject, QThread
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.match_result import MatchResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.poster_sync_port import PosterAssetSyncPort
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import (
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_rows_ready_for_plan,
)
from anivault.interfaces.gui.presenters.organizing import (
    MatchCoordinator,
    PlanApplyCoordinator,
    ScanParseCoordinator,
)
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker

logger = logging.getLogger(__name__)

PlanExecuteFn = Callable[
    [Any, Callable[[ProgressEvent], None] | None, Event],
    Any,
]
ApplyExecuteFn = Callable[
    [Any, Callable[[ProgressEvent], None] | None, Event],
    Any,
]


class OrganizerPresenter(QObject):
    """Organizer 페이지 단일 오케스트레이션: Coordinator Facade."""

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        scan_execute: Callable[[Any, object, Any], Any] | None = None,
        parse_execute: Callable[[Any, object, Any], Any] | None = None,
        match_execute: (
            Callable[
                [Any, Callable[[ProgressEvent], None] | None, Event],
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
        sync_title_groups_execute: Callable[[int], None] | None = None,
        title_match: TitleMatchRepository | None = None,
        title_groups: TitleGroupRepository | None = None,
        poster_sync: PosterAssetSyncPort | None = None,
        parent: QObject | None = None,
    ) -> None:
        """파이프라인 모델과 유스케이스 실행 콜백·진행 다이얼로그를 연결한다.

        Args:
            self: 이 프레젠터 인스턴스.
            pipeline_model: 파이프라인 테이블 모델.
            scan_execute: 스캔 유스케이스 실행 함수. None이면 스캔 비활성.
            parse_execute: 파싱 유스케이스 실행 함수. None이면 파싱 비활성.
            match_execute: 매칭 유스케이스 실행 함수. None이면 매칭 비활성.
            tmdb_search_execute: TMDB 수동 검색용 실행 함수. None이면 수동 매칭 비활성.
            plan_execute: 이동 계획 유스케이스. None이면 Dry Run 비활성.
            apply_execute: 계획 적용 유스케이스. None이면 실제 이동 불가.
            progress_dialog: 진행률 UI. None이면 다이얼로그 없음.
            include_companion_subtitles: 플랜에 동반 자막 이동을 포함할지 여부.
            sync_title_groups_execute: 파싱·캐시 완료 후 `root_id`로 title_groups 동기화.
            title_match: 포스터 로컬 경로 조회·수동 매칭 영속.
            title_groups: 수동 매칭 시 그룹–TMDB 영속.
            poster_sync: 수동 매칭 후 포스터 다운로드.
            parent: Qt 부모 객체.

        Returns:
            None.
        """
        super().__init__(parent)
        self._model = pipeline_model
        self._include_companion_subtitles = include_companion_subtitles
        self._scan_execute = scan_execute
        self._parse_execute = parse_execute
        self._match_execute = match_execute
        self._tmdb_search_execute = tmdb_search_execute
        self._plan_execute = plan_execute
        self._apply_execute = apply_execute
        self._progress_dialog = progress_dialog
        self._sync_title_groups_execute = sync_title_groups_execute
        self._title_match = title_match
        self._title_groups = title_groups
        self._poster_sync = poster_sync
        self._parse_index_root_id: int | None = None
        self._current_library_root_id: int | None = None
        self._worker_thread: QThread | None = None
        self._dry_run_enabled_handler: Callable[[bool], None] | None = None
        self._pending_plan: Any = None
        self._scan_progress_handoff_done: bool = False
        self._pipeline_panel: PipelineResultPanel | None = None
        self._tmdb_worker_keepalive: UseCaseWorker | None = None
        self._scan_parse = ScanParseCoordinator(self)
        self._match_coord = MatchCoordinator(self)
        self._plan_apply = PlanApplyCoordinator(self)

    def set_pipeline_result_panel(self, panel: PipelineResultPanel | None) -> None:
        """Pipeline Result 패널(선택 인덱스·수동 매칭 시그널)을 연결한다.

        Args:
            self: 이 프레젠터 인스턴스.
            panel: Organizer 페이지의 `PipelineResultPanel`. None이면 해제.

        Returns:
            None.
        """
        self._pipeline_panel = panel

    def _finish_worker_session(self, dialog: ProgressDialog, hide: bool) -> None:
        """워커 finished 시 세션을 닫고(무효화) 필요 시 진행 창을 숨긴다.

        Args:
            self: 이 프레젠터 인스턴스.
            dialog: 공유 ProgressDialog.
            hide: True면 hide_progress까지 호출한다.

        Returns:
            None.
        """
        dialog.mark_work_finished()
        if hide:
            dialog.hide_progress()

    def on_scan_clicked(self, path: str) -> None:
        """스캔 버튼 클릭 — `ScanParseCoordinator`에 위임한다.

        Args:
            self: 이 프레젠터 인스턴스.
            path: 스캔할 폴더 경로.

        Returns:
            None.
        """
        self._scan_parse.on_scan_clicked(path)

    def _on_scan_error(self, exc: Exception) -> None:
        """오류 시 진행 다이얼로그를 닫고 사용자에게 오류를 보여준다.

        Args:
            self: 이 프레젠터 인스턴스.
            exc: 발생한 예외.

        Returns:
            None.
        """
        logger.exception("Organizer worker failed", exc_info=exc)
        self._current_library_root_id = None
        self._parse_index_root_id = None
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        parent = self.parent()
        if isinstance(parent, QWidget):
            QMessageBox.critical(
                parent,
                "작업 오류",
                f"작업 중 오류가 발생했습니다.\n\n{exc}",
            )

    def _on_worker_finished(self, thread: QThread) -> None:
        """보관 중인 스레드와 같을 때만 워커 스레드 참조를 비운다.

        Args:
            self: 이 프레젠터 인스턴스.
            thread: 종료된 QThread.

        Returns:
            None.
        """
        if self._worker_thread is thread:
            self._worker_thread = None

    def on_match_clicked(self) -> None:
        """매칭 — `MatchCoordinator`에 위임한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        self._match_coord.on_match_clicked()

    def _parent_widget(self) -> QWidget | None:
        """Qt 부모가 QWidget이면 그 인스턴스를 반환한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            부모 위젯 또는 None.
        """
        parent = self.parent()
        return parent if isinstance(parent, QWidget) else None

    def on_manual_tmdb_match_clicked(self) -> None:
        """수동 TMDB 매칭 — `MatchCoordinator`에 위임한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        self._match_coord.on_manual_tmdb_match_clicked()

    def set_dry_run_enabled_handler(self, handler: Callable[[bool], None] | None) -> None:
        """Dry Run 버튼 활성화를 뷰에 위임한다.

        Args:
            self: 이 프레젠터 인스턴스.
            handler: True/False로 버튼 상태를 바꾸는 콜백.

        Returns:
            None.
        """
        self._dry_run_enabled_handler = handler

    def _notify_dry_run(self, enabled: bool) -> None:
        """Dry Run 버튼 상태를 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            enabled: 활성 여부.

        Returns:
            None.
        """
        if self._dry_run_enabled_handler is not None:
            self._dry_run_enabled_handler(enabled)

    def _dry_run_should_enable(self) -> bool:
        """TMDB 한글 그룹 제목이 있는 행이 하나라도 있으면 Dry Run을 켤 수 있다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            플랜 가능한 행이 있으면 True.
        """
        return bool(pipeline_rows_ready_for_plan(self._model.flat_rows()))

    def on_dry_run_clicked(self) -> None:
        """Dry Run — `PlanApplyCoordinator`에 위임한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        self._plan_apply.on_dry_run_clicked()

    def set_rows(self, rows: list[PipelineRow]) -> None:
        """파일 행을 파싱 제목 기준으로 그룹화해 파이프라인 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            rows: 평탄 파이프라인 행 목록.

        Returns:
            None.
        """
        self._model.set_rows(group_pipeline_rows(rows))
