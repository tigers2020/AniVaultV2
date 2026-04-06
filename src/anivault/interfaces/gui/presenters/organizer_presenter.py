"""organizer_presenter.py

Organizer 페이지에서 스캔·파싱·TMDB 매칭 워커를 조율하고 파이프라인 모델을 갱신한다.

Author: Pom Kim
"""

import logging
from collections.abc import Callable, Sequence
from threading import Event
from typing import Any, cast

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Slot
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.parse import ParseInput, ParseResult
from anivault.application.dto.plan import ApplyInput, ApplyResult, PlanInput, PlanResult
from anivault.application.dto.progress import ProgressEvent, progress_dialog_value_and_maximum
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.poster_sync_port import PosterAssetSyncPort
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.application.use_cases.match_series import (
    apply_tmdb_candidate_to_file_rows,
    persist_manual_tmdb_selection,
)
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.dialogs.dry_run_dialog import DryRunDialog
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_rows_ready_for_plan,
)
from anivault.interfaces.gui.presenters.plan_helpers import (
    merge_plan_into_pipeline_rows,
    pipeline_row_to_match_file,
    try_build_plan_input_from_settings,
)
from anivault.interfaces.gui.settings_storage import load_all
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

logger = logging.getLogger(__name__)

PlanExecuteFn = Callable[
    [PlanInput, Callable[[ProgressEvent], None] | None, Event],
    PlanResult,
]
ApplyExecuteFn = Callable[
    [ApplyInput, Callable[[ProgressEvent], None] | None, Event],
    ApplyResult,
]


class _ManualTmdbSearchRelay(QObject):
    """WorkerSignals를 메인 스레드의 수동 매칭 대화상자로 넘긴다(큐 연결 수신자 명시)."""

    def __init__(self, dlg: TmdbManualMatchDialog, presenter: QObject) -> None:
        """대화상자와 프레젠터(부모)를 저장한다.

        Args:
            dlg: TMDB 수동 매칭 대화상자.
            presenter: OrganizerPresenter. 릴레이의 Qt 부모(스레드 소속).

        Returns:
            None.
        """
        super().__init__(presenter)
        self._dlg = dlg

    @Slot(object)
    def on_result(self, result: object) -> None:
        """검색 결과 튜플을 목록에 반영한다.

        Args:
            result: TMDB 후보 시퀀스.

        Returns:
            None.
        """
        self._dlg.set_candidates(list(cast(Sequence[TmdbSeriesCandidateDTO], result)))

    @Slot()
    def on_finished(self) -> None:
        """워커 종료 시 검색 UI를 다시 켠다.

        Returns:
            None.
        """
        self._dlg.set_search_busy(False)
        self.deleteLater()

    @Slot(Exception)
    def on_error(self, exc: Exception) -> None:
        """검색 실패 시 메시지를 띄운다.

        Args:
            exc: 예외.

        Returns:
            None.
        """
        self._dlg.set_search_busy(False)
        QMessageBox.warning(self._dlg, "TMDB 검색 실패", str(exc))


class OrganizerPresenter(QObject):
    """Organizer 페이지 단일 오케스트레이션: 입력 검증, 워커 실행, 모델 갱신."""

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
            sync_title_groups_execute: 파싱·캐시 완료 후 `root_id`로 title_groups 동기화. None이면 생략.
            title_match: 포스터 로컬 경로 조회·수동 매칭 영속. None이면 CDN만 표시.
            title_groups: 수동 매칭 시 그룹–TMDB 영속. None이면 해당 생략.
            poster_sync: 수동 매칭 후 포스터 다운로드. None이면 생략.
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
        self._pending_plan: PlanResult | None = None
        self._scan_progress_handoff_done: bool = False
        self._pipeline_panel: PipelineResultPanel | None = None
        self._tmdb_worker_keepalive: UseCaseWorker | None = None

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
        """스캔 버튼 클릭: 경로 검증 후 워커를 시작하고 결과로 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            path: 스캔할 폴더 경로.

        Returns:
            None.
        """
        path = (path or "").strip()
        if not path:
            parent = self.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "스캔 경로 없음",
                    "스캔할 폴더를 먼저 선택해 주세요.",
                )
            return
        self._current_library_root_id = None
        self._notify_dry_run(False)
        if self._scan_execute is None:
            return
        self._scan_progress_handoff_done = False
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._scan_execute,
            input_dto=ScanInput(path=path, recursive=True),
            signals=signals,
        )
        signals.result.connect(self._on_scan_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(
                lambda: dialog.show_progress("스캔 중", "폴더 스캔 중...", True)
            )
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(
                lambda: self._on_scan_thread_finished(dialog),
            )
            signals.cancelled.connect(dialog.hide_progress)
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_scan_thread_finished(self, dialog: ProgressDialog) -> None:
        """스캔 워커 스레드 finished: 이미 파싱으로 넘겼으면 mark 생략(이중 세션 방지).

        Args:
            self: 이 프레젠터 인스턴스.
            dialog: 진행 대화상자.

        Returns:
            None.
        """
        if self._scan_progress_handoff_done:
            return
        self._finish_worker_session(dialog, hide=False)

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        """ProgressEvent로 진행 다이얼로그를 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            event: 진행률 이벤트 DTO.
            token: mark_work_started에서 캡처한 세션 토큰.

        Returns:
            None.
        """
        dialog = self._progress_dialog
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            value, maximum = progress_dialog_value_and_maximum(event)
            dialog.update_progress(
                message=event.message,
                value=value,
                maximum=maximum,
            )

    def _on_scan_result(self, result: ScanResult) -> None:
        """ScanResult를 PipelineRow로 변환해 모델에 반영한 뒤 Parse 워커를 자동 시작한다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: 스캔 유스케이스 결과.

        Returns:
            None.
        """
        self._current_library_root_id = result.index_root_id
        rows = self._scan_result_to_rows(result)
        merged = group_pipeline_rows(rows)
        if not rows or self._parse_execute is None:
            self._model.set_rows(merged)
            self._scan_progress_handoff_done = True
            if self._progress_dialog is not None:
                self._finish_worker_session(self._progress_dialog, True)
            return
        self._start_parse_worker(rows, merged, result.index_root_id)

    def _apply_scan_rows_to_model(self, merged: list[PipelineGroupRow]) -> None:
        """스캔 결과 그룹을 모델에 반영한다.

        Parse 워커의 ``started``가 메인에서 처리된 뒤 ``QTimer.singleShot(0)``으로
        한 틱 더 미룬 뒤 호출된다. 그렇지 않으면 ``QTimer(0)``가 워커 ``started``보다
        먼저 실행되어 대량 ``set_rows``가 메인을 점유하고 진행 창이 늦게 뜬다.

        Args:
            self: 이 프레젠터 인스턴스.
            merged: group_pipeline_rows 결과.

        Returns:
            None.
        """
        self._model.set_rows(merged)

    def _scan_result_to_rows(self, result: ScanResult) -> list[PipelineRow]:
        """ScanResult를 PipelineRow 목록으로 변환한다(경로·해상도 힌트 단계).

        Args:
            self: 이 프레젠터 인스턴스.
            result: 스캔 유스케이스 결과.

        Returns:
            파이프라인 행 목록.
        """
        resolutions = result.resolutions or []
        rows: list[PipelineRow] = []
        for i, p in enumerate(result.paths):
            res = resolutions[i] if i < len(resolutions) else ""
            rows.append(
                PipelineRow(
                    original_file=p,
                    parsed_title="",
                    parse_group="",
                    tmdb_korean_title_group="",
                    tmdb_series_id="",
                    tmdb_poster_path="",
                    tmdb_backdrop_path="",
                    year="",
                    season="",
                    resolution=res,
                    status="스캔됨",
                    poster_url="",
                    backdrop_url="",
                    target_path="",
                )
            )
        return rows

    def _start_parse_worker(
        self,
        scan_rows: list[PipelineRow],
        merged_groups: list[PipelineGroupRow],
        index_root_id: int | None = None,
    ) -> None:
        """Parse 워커를 시작하고, 완료 시 파싱 정보를 행에 병합해 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            scan_rows: 스캔 직후의 파이프라인 행 목록.
            merged_groups: 스캔 직후 파이프라인에 반영할 그룹 행(워커 ``started`` 이후 적용).
            index_root_id: 스캔 인덱스 루트 ID. None이면 파싱 캐시 미사용.

        Returns:
            None.
        """
        parse_execute = self._parse_execute
        if parse_execute is None:
            return
        self._parse_index_root_id = index_root_id
        paths = [r.original_file for r in scan_rows]
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=parse_execute,
            input_dto=ParseInput(paths=paths, index_root_id=index_root_id),
            signals=signals,
        )
        signals.result.connect(self._on_parse_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog

        def _on_parse_worker_started() -> None:
            """워커 run 진입 후 진행 UI를 먼저 띄우고, 다음 이벤트 루프 틱에 모델을 반영한다."""
            if dialog is not None:
                dialog.show_progress("Parse 중", "파일명 파싱 중...", False)
            QTimer.singleShot(
                0,
                lambda m=merged_groups: self._apply_scan_rows_to_model(m),
            )

        signals.started.connect(_on_parse_worker_started)
        if dialog is not None:
            self._scan_progress_handoff_done = True
            dialog.mark_work_finished()
            token = dialog.mark_work_started()
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_parse_result(self, result: ParseResult) -> None:
        """인덱스 기준으로 현재 행에 파싱 정보를 병합하고 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: 파싱 유스케이스 결과.

        Returns:
            None.
        """
        rows = self._model.flat_rows()
        parsed_list = result.parsed or []
        merged: list[PipelineRow] = []
        for i, row in enumerate(rows):
            p = parsed_list[i] if i < len(parsed_list) else None
            if p is None:
                merged.append(
                    PipelineRow(
                        original_file=row.original_file,
                        parsed_title=row.parsed_title,
                        parse_group=row.parse_group,
                        tmdb_korean_title_group=row.tmdb_korean_title_group,
                        tmdb_series_id=row.tmdb_series_id,
                        tmdb_poster_path=row.tmdb_poster_path,
                        tmdb_backdrop_path=row.tmdb_backdrop_path,
                        year=row.year,
                        season=row.season,
                        resolution=row.resolution,
                        status=row.status,
                        poster_url=row.poster_url,
                        backdrop_url=row.backdrop_url,
                        target_path=row.target_path,
                        episode=row.episode,
                    )
                )
            else:
                merged_res = (p.resolution or "").strip() or row.resolution
                merged.append(
                    PipelineRow(
                        original_file=row.original_file,
                        parsed_title=p.title,
                        parse_group=p.parse_group,
                        tmdb_korean_title_group=row.tmdb_korean_title_group,
                        tmdb_series_id=row.tmdb_series_id,
                        tmdb_poster_path=row.tmdb_poster_path,
                        tmdb_backdrop_path=row.tmdb_backdrop_path,
                        year=p.year,
                        season=p.season,
                        resolution=merged_res,
                        status="파싱됨",
                        poster_url=row.poster_url,
                        backdrop_url=row.backdrop_url,
                        target_path=row.target_path,
                        episode=p.episode,
                    )
                )
        self._model.set_rows(group_pipeline_rows(merged))
        self._notify_dry_run(False)
        root_for_sync = self._parse_index_root_id
        sync_fn = self._sync_title_groups_execute
        self._parse_index_root_id = None
        if root_for_sync is not None and sync_fn is not None:
            try:
                sync_fn(root_for_sync)
            except Exception:
                logger.exception("title_groups 동기화 실패")

    def _on_scan_error(self, exc: Exception) -> None:
        """오류 시 진행 다이얼로그를 닫고 사용자에게 오류를 보여준다.

        Args:
            self: 이 프레젠터 인스턴스.
            exc: 발생한 예외(현재 본문에서 미사용).

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

    def on_parse_clicked(self) -> None:
        """파싱 버튼 클릭(Phase 4 예약). 현재는 동작 없음.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        pass

    def on_match_clicked(self) -> None:
        """현재 평탄화된 파이프라인 행으로 TMDB 매칭 워커를 실행한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        match_execute = self._match_execute
        if match_execute is None:
            parent = self.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "TMDB API 키 없음",
                    "Settings → Parse/TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요.",
                )
            return
        self._notify_dry_run(False)
        rows = self._model.flat_rows()
        if not rows:
            parent = self.parent()
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "매칭할 항목 없음",
                    "먼저 폴더를 스캔하고 파싱이 끝난 뒤 다시 시도하세요.",
                )
            return
        files = tuple(pipeline_row_to_match_file(r) for r in rows)
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=match_execute,
            input_dto=MatchInput(files=files, index_root_id=self._current_library_root_id),
            signals=signals,
        )
        signals.result.connect(self._on_match_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(
                lambda: dialog.show_progress("TMDB 매칭", "한글 제목 조회 중…", False)
            )
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _match_file_to_pipeline_row(self, m: MatchFileRow) -> PipelineRow:
        """MatchFileRow를 PipelineRow로 변환한다.

        Args:
            self: 이 프레젠터 인스턴스.
            m: 매칭 결과 파일 행.

        Returns:
            파이프라인 테이블 행.
        """
        local_poster: str | None = None
        tm = self._title_match
        if tm is not None:
            tid_s = (m.tmdb_series_id or "").strip()
            rp = normalize_tmdb_remote_image_path(m.tmdb_poster_path)
            if tid_s and rp:
                try:
                    local_poster = tm.get_poster_local_path(int(tid_s), "poster", rp)
                except (OSError, TypeError, ValueError):
                    local_poster = None
        poster_display = resolve_final_poster_display_source(local_poster, m.poster_url)
        return PipelineRow(
            original_file=m.original_file,
            parsed_title=m.parsed_title,
            parse_group=m.parse_group,
            tmdb_korean_title_group=m.tmdb_korean_title_group,
            tmdb_series_id=m.tmdb_series_id,
            tmdb_poster_path=m.tmdb_poster_path,
            tmdb_backdrop_path=m.tmdb_backdrop_path,
            year=m.year,
            season=m.season,
            resolution=m.resolution,
            status=m.status,
            poster_url=poster_display,
            backdrop_url=m.backdrop_url,
            target_path=m.target_path,
            episode=m.episode,
        )

    def _on_match_result(self, result: MatchResult) -> None:
        """매칭 결과를 PipelineRow로 변환해 그룹화 후 모델에 반영한다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: TMDB 매칭 유스케이스 결과.

        Returns:
            None.
        """
        merged = [self._match_file_to_pipeline_row(m) for m in result.files]
        self._model.set_rows(group_pipeline_rows(merged))
        self._notify_dry_run(self._dry_run_should_enable())

    def _parent_widget(self) -> QWidget | None:
        """Qt 부모가 QWidget이면 그 인스턴스를 반환한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            부모 위젯 또는 None.
        """
        parent = self.parent()
        return parent if isinstance(parent, QWidget) else None

    def _warn_missing_tmdb_api_key(self) -> None:
        """TMDB 검색 실행 함수가 없을 때 사용자에게 안내한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        parent = self._parent_widget()
        if parent is None:
            return
        QMessageBox.warning(
            parent,
            "TMDB API 키 없음",
            "Settings → Parse/TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요.",
        )

    def _selected_pipeline_group_index_or_warn(
        self,
        panel: PipelineResultPanel,
        rows: list[PipelineGroupRow],
    ) -> int | None:
        """파이프라인에서 항목이 선택되었는지 확인하고 그룹 인덱스를 반환한다.

        Args:
            self: 이 프레젠터 인스턴스.
            panel: 파이프라인 결과 패널.
            rows: 그룹 행 목록.

        Returns:
            유효한 선택이면 인덱스, 아니면 None.
        """
        idx = panel.selected_group_index()
        if 0 <= idx < len(rows):
            return idx
        parent = self._parent_widget()
        if parent is not None:
            QMessageBox.information(
                parent,
                "선택 없음",
                "파이프라인에서 항목을 먼저 선택하세요.",
            )
        return None

    def _apply_manual_tmdb_candidate_to_model(
        self,
        group: PipelineGroupRow,
        chosen: TmdbSeriesCandidateDTO,
        panel: PipelineResultPanel,
    ) -> None:
        """수동 선택한 TMDB 후보를 그룹에 반영하고 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            group: 적용 대상 파이프라인 그룹.
            chosen: 선택된 TMDB 시리즈 후보.
            panel: 파이프라인 결과 패널.

        Returns:
            None.
        """
        target_paths = {m.original_file for m in group.members}
        flat = self._model.flat_rows()
        files_list = [pipeline_row_to_match_file(r) for r in flat]
        indices = [i for i, f in enumerate(files_list) if f.original_file in target_paths]
        if not indices:
            return
        apply_tmdb_candidate_to_file_rows(files_list, indices, chosen)
        try:
            rep_norm = normalize_path_key(files_list[indices[0]].original_file)
        except OSError:
            rep_norm = None
        persist_manual_tmdb_selection(
            files_list,
            indices,
            chosen,
            root_id=self._current_library_root_id,
            representative_path_norm=rep_norm,
            title_match=self._title_match,
            title_groups=self._title_groups,
        )
        if self._poster_sync is not None:
            self._poster_sync.sync_from_files(files_list)
        merged_rows = [self._match_file_to_pipeline_row(m) for m in files_list]
        merged_groups = group_pipeline_rows(merged_rows)
        pending_idx = 0
        for i, g in enumerate(merged_groups):
            if any(m.original_file in target_paths for m in g.members):
                pending_idx = i
                break
        panel.set_pending_selected_group_index(pending_idx)
        self._model.set_rows(merged_groups)
        self._notify_dry_run(self._dry_run_should_enable())

    def on_manual_tmdb_match_clicked(self) -> None:
        """세부 정보 패널에서 TMDB 수동 매칭을 요청한다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """

        execute = self._tmdb_search_execute
        if execute is None:
            self._warn_missing_tmdb_api_key()
            return
        panel = self._pipeline_panel
        if panel is None:
            return
        rows = self._model.rows()
        idx = self._selected_pipeline_group_index_or_warn(panel, rows)
        if idx is None:
            return
        group = rows[idx]
        default_query = (group.representative().parsed_title or "").strip()
        dlg = TmdbManualMatchDialog(parent=self._parent_widget(), default_query=default_query)
        dlg.search_requested.connect(
            lambda q, y, d=dlg: self._run_tmdb_search_worker(d, q, y),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        chosen = dlg.selected_candidate()
        if chosen is None:
            return
        self._apply_manual_tmdb_candidate_to_model(group, chosen, panel)

    def _run_tmdb_search_worker(
        self,
        dlg: TmdbManualMatchDialog,
        query: str,
        year: object,
    ) -> None:
        """다이얼로그 검색 요청에 대해 TMDB 검색 워커를 시작한다.

        Args:
            self: 이 프레젠터 인스턴스.
            dlg: 수동 매칭 대화상자.
            query: 검색어.
            year: 연도 또는 None.

        Returns:
            None.
        """
        execute = self._tmdb_search_execute
        if execute is None:
            dlg.set_search_busy(False)
            return
        q = (query or "").strip()
        if not q:
            dlg.set_search_busy(False)
            parent = self.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, "검색어 없음", "검색어를 입력하세요.")
            return
        y: int | None = year if year is None or isinstance(year, int) else None
        signals = WorkerSignals()
        relay = _ManualTmdbSearchRelay(dlg, self)
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=TmdbSearchInput(query=q, year=y),
            signals=signals,
        )
        self._tmdb_worker_keepalive = worker
        signals.result.connect(relay.on_result, type=Qt.ConnectionType.QueuedConnection)
        signals.error.connect(relay.on_error, type=Qt.ConnectionType.QueuedConnection)
        signals.finished.connect(relay.on_finished, type=Qt.ConnectionType.QueuedConnection)
        dlg.set_search_busy(True)

        def _start_tmdb_thread() -> None:
            """검색 시그널 처리 스택이 끝난 뒤 QThread를 시작한다(재진입·스케줄 이슈 회피)."""
            try:
                thread = run_worker(worker)
            except Exception:
                dlg.set_search_busy(False)
                return
            thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
            thread.finished.connect(lambda d=dlg: d.set_search_busy(False))

            def _clear_tmdb_keepalive() -> None:
                self._tmdb_worker_keepalive = None

            thread.finished.connect(_clear_tmdb_keepalive)
            self._worker_thread = thread

        QTimer.singleShot(0, _start_tmdb_thread)

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
        """Dry Run: 이동 계획 워커를 실행한 뒤 미리보기 대화상자를 연다.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        if self._plan_execute is None:
            return
        rows = self._model.flat_rows()
        settings = load_all()
        pr = settings.get("path_rules") or {}
        if not isinstance(pr, dict):
            pr = {}
        plan_input, err = try_build_plan_input_from_settings(
            rows,
            pr,
            include_companion_subtitles=self._include_companion_subtitles,
            index_root_id=self._current_library_root_id,
        )
        parent = self.parent()
        if err == "empty":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "항목 없음",
                    "먼저 스캔·매칭을 완료하세요.",
                )
            return
        if err == "no_matched":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "TMDB 매칭 없음",
                    "TMDB 한글 제목이 있는 항목이 없습니다. 자동·수동 매칭으로 준비한 뒤 다시 시도하세요.",
                )
            return
        if err == "path_rules" or plan_input is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "경로 규칙",
                    "Settings → Path Rules에서 Target root와 Path template을 설정하세요.",
                )
            return
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._plan_execute,
            input_dto=plan_input,
            signals=signals,
        )
        signals.result.connect(self._on_plan_worker_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(
                lambda: dialog.show_progress("플랜 생성", "경로 계획 중…", False)
            )
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_plan_worker_result(self, result: PlanResult) -> None:
        """플랜 결과로 Dry Run 대화상자를 띄운다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: 계획 유스케이스 결과.

        Returns:
            None.
        """
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        parent = self.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, "플랜 오류", result.error)
            self._notify_dry_run(self._dry_run_should_enable())
            return
        if not result.moves:
            if isinstance(parent, QWidget):
                QMessageBox.information(parent, "Dry Run", "이동할 항목이 없습니다.")
            self._notify_dry_run(self._dry_run_should_enable())
            return
        self._pending_plan = result
        dlg = DryRunDialog(
            [(m.source_path, m.destination_path) for m in result.moves],
            parent=parent if isinstance(parent, QWidget) else None,
        )
        dlg.apply_requested.connect(lambda: self._on_dry_run_apply_clicked(dlg))
        dlg.exec()
        self._pending_plan = None

    def _on_dry_run_apply_clicked(self, dlg: DryRunDialog) -> None:
        """미리보기에서 실제 이동을 요청한다.

        Args:
            self: 이 프레젠터 인스턴스.
            dlg: Dry Run 대화상자.

        Returns:
            None.
        """
        plan = self._pending_plan
        dlg.accept()
        parent = self.parent()
        if not plan:
            return
        if self._apply_execute is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "실제 이동 불가",
                    "실제 이동 기능이 연결되지 않았습니다. 앱을 다시 실행해 주세요.",
                )
            return
        # DryRunDialog.exec()가 끝나 중첩 이벤트 루프를 빠져나온 뒤 apply를 시작한다.
        QTimer.singleShot(0, lambda p=plan: self._start_apply_worker(p))

    def _start_apply_worker(self, plan: PlanResult) -> None:
        """apply 유스케이스 워커를 시작한다.

        Args:
            self: 이 프레젠터 인스턴스.
            plan: 실행할 계획.

        Returns:
            None.
        """
        if self._apply_execute is None:
            return
        settings = load_all()
        src_root = (settings.get("scan_build") or {}).get("source_path") or ""
        path_rules = settings.get("path_rules") or {}
        log_root = (str(src_root).strip() or path_rules.get("target_root") or "").strip()
        if not log_root:
            parent = self.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "로그 경로",
                    "스캔 소스 경로 또는 Target root를 설정해야 합니다.",
                )
            return
        apply_input = ApplyInput(
            operations=plan.moves,
            dry_run=False,
            log_root=log_root,
            source_root=str(src_root).strip() or None,
            index_root_id=self._current_library_root_id,
            organize_plan_id=plan.organize_plan_id,
            organize_item_ids=plan.organize_item_ids,
        )
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._apply_execute,
            input_dto=apply_input,
            signals=signals,
        )
        signals.result.connect(lambda r: self._on_apply_worker_result(r, plan))
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(lambda: dialog.show_progress("파일 이동", "이동 중…", False))
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel_apply() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel_apply)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_apply_worker_result(self, result: ApplyResult, plan: PlanResult) -> None:
        """적용 워커 완료 시 모델·알림을 갱신한다. 스캔 소스가 있으면 확인 후 재스캔한다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: 적용 유스케이스 결과.
            plan: 이번에 적용한 계획. 재스캔 시에는 merge에 쓰이지 않는다.

        Returns:
            None.
        """
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        parent = self.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.critical(parent, "이동 오류", result.error)
            self._notify_dry_run(self._dry_run_should_enable())
            return
        settings = load_all()
        scan_source = str((settings.get("scan_build") or {}).get("source_path") or "").strip()
        if scan_source and self._scan_execute is not None:
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "완료",
                    f"{result.moved_count}개 파일을 이동했습니다.",
                )
            self._notify_dry_run(self._dry_run_should_enable())
            self.on_scan_clicked(scan_source)
            return
        merge_plan_into_pipeline_rows(self._model, plan)
        panel = self._pipeline_panel
        if panel is not None:
            panel.sync_views_from_model()
        if isinstance(parent, QWidget):
            QMessageBox.information(
                parent,
                "완료",
                f"{result.moved_count}개 파일을 이동했습니다.",
            )
        self._notify_dry_run(self._dry_run_should_enable())

    def on_build_plan_clicked(self) -> None:
        """플랜 생성 버튼 클릭(Phase 4 예약). 현재는 동작 없음.

        Args:
            self: 이 프레젠터 인스턴스.

        Returns:
            None.
        """
        pass

    def set_rows(self, rows: list[PipelineRow]) -> None:
        """파일 행을 파싱 제목 기준으로 그룹화해 파이프라인 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            rows: 평탄 파이프라인 행 목록.

        Returns:
            None.
        """
        self._model.set_rows(group_pipeline_rows(rows))
