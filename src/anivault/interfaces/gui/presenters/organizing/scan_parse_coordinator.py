"""scan_parse_coordinator.py

스캔·파싱 워커와 파이프라인 모델 갱신을 담당한다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import partial
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.constants.gui.components import (
    PIPELINE_BUSY_MESSAGE,
    PIPELINE_BUSY_TITLE,
    SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS,
    SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_MESSAGE,
    SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_TITLE,
    SCAN_PARSE_COORDINATOR_RESULT_GROUP_CHUNK_SIZE,
    SCAN_PARSE_COORDINATOR_SCAN_PATH_EMPTY_MESSAGE,
    SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_MESSAGE_TEMPLATE,
    SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_TITLE,
    SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_MESSAGE_TEMPLATE,
    SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_TITLE,
    SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_MESSAGE,
    SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_TITLE,
    SCAN_PARSE_COORDINATOR_STATUS_PARSED,
)
from anivault.contracts.parse import ParseInput, ParseResult
from anivault.contracts.pipeline import MatchInput, MatchResult, PipelineRow
from anivault.contracts.progress import ProgressEvent, progress_dialog_value_and_maximum
from anivault.contracts.scan import ScanInput, ScanResult
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineTableModel,
    group_pipeline_rows,
)
from anivault.interfaces.gui.presenters import organizer_runtime as presenter_runtime
from anivault.interfaces.gui.presenters.row_mapper import (
    copy_pipeline_row,
    scan_path_to_pipeline_row,
)
from anivault.interfaces.gui.presenters.worker_session import (
    run_use_case_worker_with_progress_dialog,
)
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter

logger = logging.getLogger(__name__)


def _execute_title_groups_sync_worker(
    dto: int,
    progress_callback: object,
    cancel_token: Event,
    *,
    sync_fn: Callable[[int], None],
) -> None:
    """title_groups 재구성을 워커 스레드에서 실행한다.

    Args:
        dto: `library_roots.id`.
        progress_callback: 진행 콜백(미사용).
        cancel_token: 취소 토큰.
        sync_fn: 동기화 실행 콜백.

    Returns:
        None.
    """
    if cancel_token.is_set():
        return None
    sync_fn(dto)
    return None


def _execute_cached_tmdb_hydrate_worker(
    dto: MatchInput,
    progress_callback: object,
    cancel_token: Event,
    *,
    hydrate_fn: Callable[[MatchInput], MatchResult],
) -> MatchResult:
    """Run cached TMDB hydrate with the worker-compatible callable signature."""
    del progress_callback
    if cancel_token.is_set():
        return MatchResult(files=())
    return hydrate_fn(dto)


def _execute_cached_tmdb_missing_fill_worker(
    dto: MatchInput,
    progress_callback: object,
    cancel_token: Event,
    *,
    missing_fill_fn: Callable[[MatchInput, object, Event], MatchResult],
) -> MatchResult:
    """Run cached TMDB missing-fill with the worker-compatible callable signature."""
    return missing_fill_fn(dto, progress_callback, cancel_token)


class ScanParseCoordinator(QObject):
    """스캔→파싱 흐름과 진행 다이얼로그 세션."""

    def __init__(self, presenter: OrganizerPresenter) -> None:
        """호스트 프레젠터를 부모 QObject로 둔다.

        Args:
            presenter: OrganizerPresenter 인스턴스.

        Returns:
            None.
        """
        super().__init__(presenter)
        self._p = presenter
        self._parse_apply_generation = 0
        # 파싱 완료 시 병합용: 대용량에서 중간 set_rows를 생략하면 모델이 비어 있을 수 있음.
        self._parse_snapshot: tuple[int, list[PipelineRow]] | None = None
        self._pending_cached_hydrate: dict[int, tuple[PipelineTableModel, MatchInput]] = {}
        self._pending_cached_missing_fill: dict[int, tuple[PipelineTableModel, MatchInput]] = {}

    def _warn_scan_path(self, title: str, message: str) -> None:
        """부모가 QWidget이면 경고 대화상자를 띄운다.

        Args:
            self: 이 코디네이터.
            title: 창 제목.
            message: 본문.

        Returns:
            None.
        """
        parent = presenter_runtime.parent_widget(self._p)
        if isinstance(parent, QWidget):
            QMessageBox.warning(parent, title, message)

    def _clear_stale_progress_dialog(self) -> None:
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is None or presenter_runtime.has_active_pipeline_work(self._p):
            return
        presenter_runtime.finish_worker_session(self._p, dialog, hide=True)

    def _scan_path_is_usable_directory(self, path: str) -> bool:
        """스캔 루트가 열 수 있는 디렉터리면 True, 아니면 경고 후 False.

        Args:
            self: 이 코디네이터.
            path: 검사할 경로(비어 있지 않음).

        Returns:
            스캔을 시작해도 되면 True.
        """
        try:
            if Path(path).is_dir():
                return True
        except OSError as e:
            self._warn_scan_path(
                SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_TITLE,
                SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_MESSAGE_TEMPLATE.format(
                    path=path,
                    error=e,
                ),
            )
            return False
        self._warn_scan_path(
            SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_TITLE,
            SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_MESSAGE_TEMPLATE.format(path=path),
        )
        return False

    def on_scan_clicked(self, path: str) -> None:
        """스캔 버튼 클릭: 경로 검증 후 워커를 시작하고 결과로 모델을 갱신한다.

        Args:
            path: 스캔할 폴더 경로.

        Returns:
            None.
        """
        path = (path or "").strip()
        if not path:
            self._clear_stale_progress_dialog()
            self._warn_scan_path(
                SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_TITLE,
                SCAN_PARSE_COORDINATOR_SCAN_PATH_EMPTY_MESSAGE,
            )
            return
        if not self._scan_path_is_usable_directory(path):
            self._clear_stale_progress_dialog()
            return
        if presenter_runtime.has_active_pipeline_work(self._p):
            parent = presenter_runtime.parent_widget(self._p)
            if isinstance(parent, QWidget):
                QMessageBox.information(parent, PIPELINE_BUSY_TITLE, PIPELINE_BUSY_MESSAGE)
            return
        self._start_scan_worker(path)

    def run_scan_after_apply_completion(self, path: str) -> None:
        """적용 완료 후 자동 재스캔: 사용자 가드 없이 동일 스캔 파이프라인을 시작한다."""

        p = (path or "").strip()
        if not p:
            return
        if not self._scan_path_is_usable_directory(p):
            return
        self._start_scan_worker(p)

    def _start_scan_worker(self, path: str) -> None:
        presenter_runtime.set_current_library_root_id(self._p, None)
        execute = presenter_runtime.scan_execute(self._p)
        if execute is None:
            return
        presenter_runtime.set_scan_progress_handoff_done(self._p, False)
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=ScanInput(
                path=path,
                recursive=True,
                exclude_subtitles_with_paired_video=presenter_runtime.exclude_subtitles_with_paired_video(
                    self._p
                ),
            ),
            signals=signals,
        )
        signals.result.connect(self._on_scan_result)
        signals.error.connect(lambda exc: presenter_runtime.on_scan_error(self._p, exc))
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_TITLE,
                message=SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_MESSAGE,
                indeterminate=True,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._on_scan_thread_finished(dialog),
            )
        else:
            thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)

    def _on_scan_thread_finished(self, dialog: ProgressDialog) -> None:
        """스캔 워커 스레드 finished: 이미 파싱으로 넘겼으면 mark 생략.

        Args:
            dialog: 진행 대화상자.

        Returns:
            None.
        """
        if presenter_runtime.scan_progress_handoff_done(self._p):
            return
        presenter_runtime.finish_worker_session(self._p, dialog, hide=False)

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        """ProgressEvent로 진행 다이얼로그를 갱신한다.

        Args:
            event: 진행률 이벤트 DTO.
            token: mark_work_started에서 캡처한 세션 토큰.

        Returns:
            None.
        """
        dialog = presenter_runtime.progress_dialog(self._p)
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
            result: 스캔 유스케이스 결과.

        Returns:
            None.
        """
        presenter_runtime.set_current_library_root_id(self._p, result.index_root_id)
        rows = self._scan_result_to_rows(result)
        merged = group_pipeline_rows(rows)
        if not rows or presenter_runtime.parse_execute(self._p) is None:
            presenter_runtime.model(self._p).set_rows(merged)
            presenter_runtime.set_scan_progress_handoff_done(self._p, True)
            dialog = presenter_runtime.progress_dialog(self._p)
            if dialog is not None:
                presenter_runtime.finish_worker_session(self._p, dialog, hide=True)
            return
        self._start_parse_worker(rows, merged, result.index_root_id)

    def _apply_scan_rows_to_model(self, merged: list[PipelineGroupRow]) -> None:
        """스캔 결과 그룹을 모델에 반영한다.

        Args:
            merged: group_pipeline_rows 결과.

        Returns:
            None.
        """
        presenter_runtime.model(self._p).set_rows(merged)

    def _scan_result_to_rows(self, result: ScanResult) -> list[PipelineRow]:
        """ScanResult를 PipelineRow 목록으로 변환한다.

        Args:
            result: 스캔 유스케이스 결과.

        Returns:
            파이프라인 행 목록.
        """
        resolutions = result.resolutions or []
        rows: list[PipelineRow] = []
        for i, p in enumerate(result.paths):
            res = resolutions[i] if i < len(resolutions) else ""
            rows.append(scan_path_to_pipeline_row(p, res))
        return rows

    def _start_parse_worker(
        self,
        scan_rows: list[PipelineRow],
        merged_groups: list[PipelineGroupRow],
        index_root_id: int | None = None,
    ) -> None:
        """Parse 워커를 시작하고, 완료 시 파싱 정보를 행에 병합해 모델을 갱신한다.

        Args:
            scan_rows: 스캔 직후의 파이프라인 행 목록.
            merged_groups: 스캔 직후 파이프라인에 반영할 그룹 행.
            index_root_id: 스캔 인덱스 루트 ID.

        Returns:
            None.
        """
        parse_execute = presenter_runtime.parse_execute(self._p)
        if parse_execute is None:
            return
        presenter_runtime.set_parse_index_root_id(self._p, index_root_id)
        paths = [r.original_file for r in scan_rows]
        self._parse_apply_generation += 1
        session_gen = self._parse_apply_generation
        self._parse_snapshot = (session_gen, list(scan_rows))
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=parse_execute,
            input_dto=ParseInput(paths=paths, index_root_id=index_root_id),
            signals=signals,
        )
        signals.result.connect(lambda res, g=session_gen: self._on_parse_result(res, g))
        signals.error.connect(lambda exc: presenter_runtime.on_scan_error(self._p, exc))
        dialog = presenter_runtime.progress_dialog(self._p)

        def _on_parse_worker_started() -> None:
            """워커 run 진입 후 진행 UI를 먼저 띄우고, 다음 틱에 모델을 반영한다."""
            n_groups = len(merged_groups)
            if n_groups <= SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS:
                QTimer.singleShot(
                    0,
                    lambda m=merged_groups: self._apply_scan_rows_to_model(m),
                )
            else:
                logger.debug(
                    "skip mid-scan model apply: groups=%s > %s",
                    n_groups,
                    SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS,
                )

        if dialog is not None:
            presenter_runtime.set_scan_progress_handoff_done(self._p, True)
            dialog.mark_work_finished()
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_TITLE,
                message=SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: presenter_runtime.finish_worker_session(
                    self._p,
                    dialog,
                    hide=True,
                ),
                on_started=_on_parse_worker_started,
                hide_progress_on_cancelled=False,
            )
        else:
            thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)

    def _on_parse_result(self, result: ParseResult, session_gen: int) -> None:
        """인덱스 기준으로 현재 행에 파싱 정보를 병합하고 모델을 갱신한다.

        Args:
            result: 파싱 유스케이스 결과.
            session_gen: `_start_parse_worker`에서 부여한 세대. 더 새 파싱이 있으면 무시.

        Returns:
            None.
        """
        if session_gen != self._parse_apply_generation:
            return
        model: PipelineTableModel = presenter_runtime.model(self._p)
        if self._parse_snapshot is not None and self._parse_snapshot[0] == session_gen:
            rows = self._parse_snapshot[1]
            self._parse_snapshot = None
        else:
            rows = model.flat_rows()
        parsed_list = result.parsed or []
        merged: list[PipelineRow] = []
        for i, row in enumerate(rows):
            p = parsed_list[i] if i < len(parsed_list) else None
            if p is None:
                merged.append(copy_pipeline_row(row))
            else:
                merged_res = (p.resolution or "").strip() or row.resolution
                merged.append(
                    copy_pipeline_row(
                        row,
                        parsed_title=p.title,
                        parse_group=p.parse_group,
                        year=p.year,
                        season=p.season,
                        resolution=merged_res,
                        status=SCAN_PARSE_COORDINATOR_STATUS_PARSED,
                        episode=p.episode,
                    )
                )
        root_for_sync = presenter_runtime.parse_index_root_id(self._p)
        sync_fn = presenter_runtime.sync_title_groups_execute(self._p)
        presenter_runtime.set_parse_index_root_id(self._p, None)
        self._apply_parse_result_rows_after_optional_hydrate(
            model,
            merged,
            session_gen=session_gen,
            root_for_sync=root_for_sync,
            sync_fn=sync_fn,
        )

    def _apply_parse_result_rows_after_optional_hydrate(
        self,
        model: PipelineTableModel,
        merged: list[PipelineRow],
        *,
        session_gen: int,
        root_for_sync: int | None,
        sync_fn: Callable[[int], None] | None,
    ) -> None:
        """Hydrate cached TMDB data off the UI thread, then apply rows in chunks."""
        hydrate_fn = presenter_runtime.cached_tmdb_hydrate_execute(self._p)
        missing_fill_fn = presenter_runtime.cached_tmdb_missing_fill_execute(self._p)
        if root_for_sync is not None and hydrate_fn is not None:
            self._pending_cached_hydrate[session_gen] = (
                model,
                MatchInput(
                    files=tuple(merged),
                    index_root_id=root_for_sync,
                ),
            )
        if root_for_sync is not None and missing_fill_fn is not None:
            self._pending_cached_missing_fill[session_gen] = (
                model,
                MatchInput(
                    files=tuple(merged),
                    index_root_id=root_for_sync,
                ),
            )
        self._apply_parse_result_groups_chunked(
            model,
            group_pipeline_rows(merged),
            session_gen=session_gen,
            root_for_sync=root_for_sync,
            sync_fn=sync_fn,
        )

    def _run_pending_cached_tmdb_hydrate(self, session_gen: int) -> bool:
        """Start cached TMDB hydrate after parsed rows are already visible.

        Returns:
            True if a background worker was started, False otherwise.
        """
        hydrate_fn = presenter_runtime.cached_tmdb_hydrate_execute(self._p)
        pending = self._pending_cached_hydrate.pop(session_gen, None)
        if pending is None or hydrate_fn is None or session_gen != self._parse_apply_generation:
            return False
        model, hydrate_input = pending

        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=partial(_execute_cached_tmdb_hydrate_worker, hydrate_fn=hydrate_fn),
            input_dto=hydrate_input,
            signals=signals,
        )
        signals.result.connect(
            lambda result, g=session_gen: self._on_cached_tmdb_hydrate_result(
                result,
                model,
                g,
            )
        )
        signals.error.connect(
            lambda exc, lg=logger: lg.exception("cached TMDB hydrate failed", exc_info=exc)
        )
        thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)
        return True

    def _on_cached_tmdb_hydrate_result(
        self,
        result: MatchResult,
        model: PipelineTableModel,
        session_gen: int,
    ) -> None:
        """Apply cached TMDB hydrate results after the background worker completes."""
        if session_gen != self._parse_apply_generation:
            return
        grouped = group_pipeline_rows(
            [
                presenter_runtime.map_match_file_to_pipeline_row(self._p, file)
                for file in result.files
            ]
        )
        self._pending_cached_missing_fill[session_gen] = (
            model,
            MatchInput(
                files=tuple(result.files),
                index_root_id=presenter_runtime.current_library_root_id(self._p),
            ),
        )
        self._apply_parse_result_groups_chunked(
            model,
            grouped,
            session_gen=session_gen,
            root_for_sync=None,
            sync_fn=None,
        )

    def _run_pending_cached_tmdb_missing_fill(self, session_gen: int) -> bool:
        """Start cached TMDB missing-fill worker for rows with missing metadata/posters.

        Returns:
            True if a background worker was started, False otherwise.
        """
        missing_fill_fn = presenter_runtime.cached_tmdb_missing_fill_execute(self._p)
        pending = self._pending_cached_missing_fill.pop(session_gen, None)
        if (
            pending is None
            or missing_fill_fn is None
            or session_gen != self._parse_apply_generation
        ):
            return False
        model, missing_fill_input = pending

        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=partial(
                _execute_cached_tmdb_missing_fill_worker,
                missing_fill_fn=missing_fill_fn,
            ),
            input_dto=missing_fill_input,
            signals=signals,
        )
        signals.result.connect(
            lambda result, g=session_gen: self._on_cached_tmdb_missing_fill_result(
                result,
                model,
                g,
            )
        )
        signals.error.connect(
            lambda exc, lg=logger: lg.exception("cached TMDB missing fill failed", exc_info=exc)
        )
        thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)
        return True

    def _on_cached_tmdb_missing_fill_result(
        self,
        result: MatchResult,
        model: PipelineTableModel,
        session_gen: int,
    ) -> None:
        """Apply missing-filled rows after the background worker completes."""
        if session_gen != self._parse_apply_generation:
            return
        grouped = group_pipeline_rows(
            [
                presenter_runtime.map_match_file_to_pipeline_row(self._p, file)
                for file in result.files
            ]
        )
        self._apply_parse_result_groups_chunked(
            model,
            grouped,
            session_gen=session_gen,
            root_for_sync=None,
            sync_fn=None,
        )

    def _after_parse_result_groups_applied(
        self,
        *,
        session_gen: int,
        root_for_sync: int | None,
        sync_fn: Callable[[int], None] | None,
    ) -> None:
        """파싱 청크 적용 완료 후 뷰 동기화·알림·선택적 title_groups 워커를 수행한다.

        Args:
            root_for_sync: `title_groups` 동기화용 루트 id.
            sync_fn: 동기화 실행 콜백.

        Returns:
            None.
        """
        # append_row_groups는 rowsInserted만 발생 → 패널은 modelReset에서만 분할 뷰 동기화.
        panel = presenter_runtime.pipeline_panel(self._p)
        if panel is not None:
            panel.sync_views_from_model()
        presenter_runtime.notify_dry_run(self._p, False)
        has_pending_hydrate = session_gen in self._pending_cached_hydrate
        started_hydrate = self._run_pending_cached_tmdb_hydrate(session_gen)
        started_missing = False
        if not has_pending_hydrate:
            started_missing = self._run_pending_cached_tmdb_missing_fill(session_gen)
        if not started_hydrate and not started_missing:
            presenter_runtime.notify_dry_run(
                self._p,
                presenter_runtime.dry_run_should_enable(self._p),
            )
        if root_for_sync is None or sync_fn is None:
            return
        self._run_title_groups_sync_worker(root_for_sync, sync_fn)

    def _run_title_groups_sync_worker(
        self, root_for_sync: int, sync_fn: Callable[[int], None]
    ) -> None:
        """title_groups 동기화를 백그라운드 스레드에서 시작한다.

        Args:
            root_for_sync: `library_roots.id`.
            sync_fn: 동기화 실행 콜백.

        Returns:
            None.
        """
        signals = WorkerSignals()
        # parent 없음: 부모가 있는 QObject는 moveToThread 불가(Qt 경고).
        worker = UseCaseWorker(
            execute_fn=partial(_execute_title_groups_sync_worker, sync_fn=sync_fn),
            input_dto=root_for_sync,
            signals=signals,
        )
        signals.error.connect(
            lambda exc, lg=logger: lg.exception(
                "title_groups 동기화 실패",
                exc_info=exc,
            ),
        )
        thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)

    def _schedule_parse_result_chunk_work(
        self,
        model: PipelineTableModel,
        grouped: list[PipelineGroupRow],
        *,
        session_gen: int,
        chunk_sz: int,
        n: int,
        idx_ref: list[int],
        root_for_sync: int | None,
        sync_fn: Callable[[int], None] | None,
    ) -> None:
        """한 청크를 모델에 붙이거나, 끝나면 후처리·다음 타이머를 예약한다.

        Args:
            model: 파이프라인 테이블 모델.
            grouped: 그룹 행 전체.
            session_gen: 진행 중 파싱 세대.
            chunk_sz: 청크 크기.
            n: 그룹 개수.
            idx_ref: 현재 인덱스(단일 원소 리스트, 재진입 시 갱신용).
            root_for_sync: title_groups 동기화 루트.
            sync_fn: 동기화 콜백.

        Returns:
            None.
        """
        if session_gen != self._parse_apply_generation:
            return
        if idx_ref[0] >= n:
            self._after_parse_result_groups_applied(
                session_gen=session_gen,
                root_for_sync=root_for_sync,
                sync_fn=sync_fn,
            )
            return
        end = min(idx_ref[0] + chunk_sz, n)
        model.append_row_groups(grouped[idx_ref[0] : end])
        idx_ref[0] = end
        if idx_ref[0] >= n:
            self._after_parse_result_groups_applied(
                session_gen=session_gen,
                root_for_sync=root_for_sync,
                sync_fn=sync_fn,
            )
        else:
            QTimer.singleShot(
                0,
                partial(
                    self._schedule_parse_result_chunk_work,
                    model,
                    grouped,
                    session_gen=session_gen,
                    chunk_sz=chunk_sz,
                    n=n,
                    idx_ref=idx_ref,
                    root_for_sync=root_for_sync,
                    sync_fn=sync_fn,
                ),
            )

    def _apply_parse_result_groups_chunked(
        self,
        model: PipelineTableModel,
        grouped: list[PipelineGroupRow],
        *,
        session_gen: int,
        root_for_sync: int | None,
        sync_fn: Callable[[int], None] | None,
    ) -> None:
        """파싱 그룹을 청크로 모델에 붙인 뒤, 끝나면 동기화 워커를 연다.

        Args:
            model: 파이프라인 테이블 모델.
            grouped: 전체 그룹 행(순서·병합은 `group_pipeline_rows` 완료본).
            session_gen: 진행 중 파싱 세대. 불일치 시 중단.
            root_for_sync: `title_groups` 동기화용 루트 id.
            sync_fn: 동기화 실행 콜백. None이면 생략.

        Returns:
            None.
        """
        chunk_sz = SCAN_PARSE_COORDINATOR_RESULT_GROUP_CHUNK_SIZE
        n = len(grouped)
        idx_ref = [0]
        model.clear_with_reset()
        self._schedule_parse_result_chunk_work(
            model,
            grouped,
            session_gen=session_gen,
            chunk_sz=chunk_sz,
            n=n,
            idx_ref=idx_ref,
            root_for_sync=root_for_sync,
            sync_fn=sync_fn,
        )
