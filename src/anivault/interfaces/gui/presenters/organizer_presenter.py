"""organizer_presenter.py

Organizer 페이지에서 스캔·파싱·TMDB 매칭 워커를 조율하고 파이프라인 모델을 갱신한다.

Author: Pom Kim
"""

from collections.abc import Callable
from threading import Event
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QThread
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.parse import ParseInput, ParseResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel, group_pipeline_rows
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog


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
        progress_dialog: "ProgressDialog | None" = None,
        parent: QObject | None = None,
    ) -> None:
        """파이프라인 모델과 유스케이스 실행 콜백·진행 다이얼로그를 연결한다.

        Args:
            self: 이 프레젠터 인스턴스.
            pipeline_model: 파이프라인 테이블 모델.
            scan_execute: 스캔 유스케이스 실행 함수. None이면 스캔 비활성.
            parse_execute: 파싱 유스케이스 실행 함수. None이면 파싱 비활성.
            match_execute: 매칭 유스케이스 실행 함수. None이면 매칭 비활성.
            progress_dialog: 진행률 UI. None이면 다이얼로그 없음.
            parent: Qt 부모 객체.

        Returns:
            None.
        """
        super().__init__(parent)
        self._model = pipeline_model
        self._scan_execute = scan_execute
        self._parse_execute = parse_execute
        self._match_execute = match_execute
        self._progress_dialog = progress_dialog
        self._worker_thread: QThread | None = None

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
        if self._scan_execute is None:
            return
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
            signals.started.connect(
                lambda: dialog.show_progress("스캔 중", "폴더 스캔 중...", True)
            )
            signals.progress.connect(self._on_progress)
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

    def _on_progress(self, event: ProgressEvent) -> None:
        """ProgressEvent로 진행 다이얼로그를 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            event: 진행률 이벤트 DTO.

        Returns:
            None.
        """
        if self._progress_dialog is not None:
            self._progress_dialog.update_progress(
                message=event.message,
                value=event.percent if event.total > 0 else None,
                maximum=event.total if event.total > 0 else 100,
            )

    def _on_scan_result(self, result: ScanResult) -> None:
        """ScanResult를 PipelineRow로 변환해 모델에 반영한 뒤 Parse 워커를 자동 시작한다.

        Args:
            self: 이 프레젠터 인스턴스.
            result: 스캔 유스케이스 결과.

        Returns:
            None.
        """
        rows = self._scan_result_to_rows(result)
        self._model.set_rows(group_pipeline_rows(rows))
        if not rows or self._parse_execute is None:
            if self._progress_dialog is not None:
                self._progress_dialog.hide_progress()
            return
        self._start_parse_worker(rows)

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

    def _start_parse_worker(self, scan_rows: list[PipelineRow]) -> None:
        """Parse 워커를 시작하고, 완료 시 파싱 정보를 행에 병합해 모델을 갱신한다.

        Args:
            self: 이 프레젠터 인스턴스.
            scan_rows: 스캔 직후의 파이프라인 행 목록.

        Returns:
            None.
        """
        parse_execute = self._parse_execute
        if parse_execute is None:
            return
        paths = [r.original_file for r in scan_rows]
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=parse_execute,
            input_dto=ParseInput(paths=paths),
            signals=signals,
        )
        signals.result.connect(self._on_parse_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            signals.started.connect(
                lambda: dialog.show_progress("Parse 중", "파일명 파싱 중...", False)
            )
            signals.progress.connect(self._on_progress)
            signals.finished.connect(dialog.hide_progress)
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
                    )
                )
        self._model.set_rows(group_pipeline_rows(merged))

    def _on_scan_error(self, exc: Exception) -> None:
        """오류 시 모델은 유지하고 진행 다이얼로그만 숨긴다.

        Args:
            self: 이 프레젠터 인스턴스.
            exc: 발생한 예외(현재 본문에서 미사용).

        Returns:
            None.
        """
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()

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
        files = tuple(self._pipeline_row_to_match_file(r) for r in rows)
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=match_execute,
            input_dto=MatchInput(files=files),
            signals=signals,
        )
        signals.result.connect(self._on_match_result)
        signals.error.connect(self._on_scan_error)
        dialog = self._progress_dialog
        if dialog is not None:
            signals.started.connect(
                lambda: dialog.show_progress("TMDB 매칭", "한글 제목 조회 중…", False)
            )
            signals.progress.connect(self._on_progress)
            signals.finished.connect(dialog.hide_progress)
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

    def _pipeline_row_to_match_file(self, row: PipelineRow) -> MatchFileRow:
        """PipelineRow를 MatchFileRow DTO로 변환한다.

        Args:
            self: 이 프레젠터 인스턴스.
            row: 파이프라인 테이블 행.

        Returns:
            매칭 입력용 파일 행.
        """
        return MatchFileRow(
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
        )

    def _match_file_to_pipeline_row(self, m: MatchFileRow) -> PipelineRow:
        """MatchFileRow를 PipelineRow로 변환한다.

        Args:
            self: 이 프레젠터 인스턴스.
            m: 매칭 결과 파일 행.

        Returns:
            파이프라인 테이블 행.
        """
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
            poster_url=m.poster_url,
            backdrop_url=m.backdrop_url,
            target_path=m.target_path,
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
