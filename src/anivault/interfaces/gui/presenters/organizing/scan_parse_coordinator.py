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
    run_use_case_worker_with_progress_dialog,
)
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter

logger = logging.getLogger(__name__)

PARSE_RESULT_GROUP_CHUNK_SIZE = 96
# 스캔 직후·파싱 중간에 테이블을 한 번 더 그리면 대용량에서 modelReset 비용이 두 번 든다.
PARSE_MID_SCAN_MODEL_MAX_GROUPS = 1000


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

    def _warn_scan_path(self, title: str, message: str) -> None:
        """부모가 QWidget이면 경고 대화상자를 띄운다.

        Args:
            self: 이 코디네이터.
            title: 창 제목.
            message: 본문.

        Returns:
            None.
        """
        parent = self._p.parent()
        if isinstance(parent, QWidget):
            QMessageBox.warning(parent, title, message)

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
                "스캔 경로 오류",
                "지정한 폴더에 접근할 수 없습니다(네트워크·권한·이동된 드라이브 등).\n\n"
                f"{path}\n\n{e}",
            )
            return False
        self._warn_scan_path(
            "스캔 경로 없음",
            f"폴더가 없거나 접근할 수 없습니다. 경로를 확인하거나 다시 선택하세요.\n\n{path}",
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
            self._warn_scan_path("스캔 경로 없음", "스캔할 폴더를 먼저 선택해 주세요.")
            return
        if not self._scan_path_is_usable_directory(path):
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
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title="스캔 중",
                message="폴더 스캔 중...",
                indeterminate=True,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._on_scan_thread_finished(dialog),
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p.register_worker_thread(thread)  # noqa: SLF001

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
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001

        def _on_parse_worker_started() -> None:
            """워커 run 진입 후 진행 UI를 먼저 띄우고, 다음 틱에 모델을 반영한다."""
            n_groups = len(merged_groups)
            if n_groups <= PARSE_MID_SCAN_MODEL_MAX_GROUPS:
                QTimer.singleShot(
                    0,
                    lambda m=merged_groups: self._apply_scan_rows_to_model(m),
                )
            else:
                logger.debug(
                    "skip mid-scan model apply: groups=%s > %s",
                    n_groups,
                    PARSE_MID_SCAN_MODEL_MAX_GROUPS,
                )

        if dialog is not None:
            self._p._scan_progress_handoff_done = True  # noqa: SLF001
            dialog.mark_work_finished()
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title="Parse 중",
                message="파일명 파싱 중...",
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
                on_started=_on_parse_worker_started,
                hide_progress_on_cancelled=False,
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p.register_worker_thread(thread)  # noqa: SLF001

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
        model: PipelineTableModel = self._p._model  # noqa: SLF001
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
        grouped = group_pipeline_rows(merged)
        root_for_sync = self._p._parse_index_root_id  # noqa: SLF001
        sync_fn = self._p._sync_title_groups_execute  # noqa: SLF001
        self._p._parse_index_root_id = None  # noqa: SLF001
        self._apply_parse_result_groups_chunked(
            model,
            grouped,
            session_gen=session_gen,
            root_for_sync=root_for_sync,
            sync_fn=sync_fn,
        )

    def _after_parse_result_groups_applied(
        self,
        *,
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
        panel = self._p._pipeline_panel  # noqa: SLF001
        if panel is not None:
            panel.sync_views_from_model()
        self._p._notify_dry_run(False)  # noqa: SLF001
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
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p.register_worker_thread(thread)  # noqa: SLF001

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
                root_for_sync=root_for_sync,
                sync_fn=sync_fn,
            )
            return
        end = min(idx_ref[0] + chunk_sz, n)
        model.append_row_groups(grouped[idx_ref[0] : end])
        idx_ref[0] = end
        if idx_ref[0] >= n:
            self._after_parse_result_groups_applied(
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
        chunk_sz = PARSE_RESULT_GROUP_CHUNK_SIZE
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
