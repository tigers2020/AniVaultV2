"""scan_parse_coordinator.py

스캔·파싱 워커와 파이프라인 모델 갱신을 담당한다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.parse import ParseInput, ParseResult
from anivault.application.dto.progress import ProgressEvent, progress_dialog_value_and_maximum
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
)
from anivault.interfaces.gui.presenters.worker_session import (
    disconnect_worker_cancel_on_thread_finished,
)
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter

logger = logging.getLogger(__name__)


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

    def on_scan_clicked(self, path: str) -> None:
        """스캔 버튼 클릭: 경로 검증 후 워커를 시작하고 결과로 모델을 갱신한다.

        Args:
            path: 스캔할 폴더 경로.

        Returns:
            None.
        """
        path = (path or "").strip()
        if not path:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "스캔 경로 없음",
                    "스캔할 폴더를 먼저 선택해 주세요.",
                )
            return
        self._p._current_library_root_id = None  # noqa: SLF001
        self._p._notify_dry_run(False)  # noqa: SLF001
        if self._p._scan_execute is None:  # noqa: SLF001
            return
        self._p._scan_progress_handoff_done = False  # noqa: SLF001
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._p._scan_execute,  # noqa: SLF001
            input_dto=ScanInput(path=path, recursive=True),
            signals=signals,
        )
        signals.result.connect(self._on_scan_result)
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001
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
            thread = run_worker(worker)
            disconnect_worker_cancel_on_thread_finished(dialog, worker, thread)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_scan_thread_finished(self, dialog: ProgressDialog) -> None:
        """스캔 워커 스레드 finished: 이미 파싱으로 넘겼으면 mark 생략.

        Args:
            dialog: 진행 대화상자.

        Returns:
            None.
        """
        if self._p._scan_progress_handoff_done:  # noqa: SLF001
            return
        self._p._finish_worker_session(dialog, hide=False)  # noqa: SLF001

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        """ProgressEvent로 진행 다이얼로그를 갱신한다.

        Args:
            event: 진행률 이벤트 DTO.
            token: mark_work_started에서 캡처한 세션 토큰.

        Returns:
            None.
        """
        dialog = self._p._progress_dialog  # noqa: SLF001
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
        self._p._current_library_root_id = result.index_root_id  # noqa: SLF001
        rows = self._scan_result_to_rows(result)
        merged = group_pipeline_rows(rows)
        if not rows or self._p._parse_execute is None:  # noqa: SLF001
            self._p._model.set_rows(merged)  # noqa: SLF001
            self._p._scan_progress_handoff_done = True  # noqa: SLF001
            if self._p._progress_dialog is not None:  # noqa: SLF001
                self._p._finish_worker_session(self._p._progress_dialog, True)  # noqa: SLF001
            return
        self._start_parse_worker(rows, merged, result.index_root_id)

    def _apply_scan_rows_to_model(self, merged: list[PipelineGroupRow]) -> None:
        """스캔 결과 그룹을 모델에 반영한다.

        Args:
            merged: group_pipeline_rows 결과.

        Returns:
            None.
        """
        self._p._model.set_rows(merged)  # noqa: SLF001

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
            scan_rows: 스캔 직후의 파이프라인 행 목록.
            merged_groups: 스캔 직후 파이프라인에 반영할 그룹 행.
            index_root_id: 스캔 인덱스 루트 ID.

        Returns:
            None.
        """
        parse_execute = self._p._parse_execute  # noqa: SLF001
        if parse_execute is None:
            return
        self._p._parse_index_root_id = index_root_id  # noqa: SLF001
        paths = [r.original_file for r in scan_rows]
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=parse_execute,
            input_dto=ParseInput(paths=paths, index_root_id=index_root_id),
            signals=signals,
        )
        signals.result.connect(self._on_parse_result)
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001

        def _on_parse_worker_started() -> None:
            """워커 run 진입 후 진행 UI를 먼저 띄우고, 다음 틱에 모델을 반영한다."""
            if dialog is not None:
                dialog.show_progress("Parse 중", "파일명 파싱 중...", False)
            QTimer.singleShot(
                0,
                lambda m=merged_groups: self._apply_scan_rows_to_model(m),
            )

        signals.started.connect(_on_parse_worker_started)
        if dialog is not None:
            self._p._scan_progress_handoff_done = True  # noqa: SLF001
            dialog.mark_work_finished()
            token = dialog.mark_work_started()
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(
                lambda: self._p._finish_worker_session(dialog, True)
            )  # noqa: SLF001
            dialog.canceled.connect(worker.cancel)
            thread = run_worker(worker)
            disconnect_worker_cancel_on_thread_finished(dialog, worker, thread)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_parse_result(self, result: ParseResult) -> None:
        """인덱스 기준으로 현재 행에 파싱 정보를 병합하고 모델을 갱신한다.

        Args:
            result: 파싱 유스케이스 결과.

        Returns:
            None.
        """
        model: PipelineTableModel = self._p._model  # noqa: SLF001
        rows = model.flat_rows()
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
        model.set_rows(group_pipeline_rows(merged))
        self._p._notify_dry_run(False)  # noqa: SLF001
        root_for_sync = self._p._parse_index_root_id  # noqa: SLF001
        sync_fn = self._p._sync_title_groups_execute  # noqa: SLF001
        self._p._parse_index_root_id = None  # noqa: SLF001
        if root_for_sync is not None and sync_fn is not None:
            try:
                sync_fn(root_for_sync)
            except Exception:
                logger.exception("title_groups 동기화 실패")
