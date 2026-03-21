"""OrganizerPresenter: orchestrates OrganizerPage <-> scan/match/plan use cases."""

from collections.abc import Callable
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
    """Single orchestration for Organizer page. Validates input, runs workers, updates model."""

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        scan_execute: Callable[[ScanInput, object, Any], ScanResult] | None = None,
        parse_execute: Callable[[ParseInput, object, Any], ParseResult] | None = None,
        match_execute: Callable[[MatchInput, object, Any], MatchResult] | None = None,
        progress_dialog: "ProgressDialog | None" = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = pipeline_model
        self._scan_execute = scan_execute
        self._parse_execute = parse_execute
        self._match_execute = match_execute
        self._progress_dialog = progress_dialog
        self._worker_thread: QThread | None = None

    def on_scan_clicked(self, path: str) -> None:
        """Handle scan button click. Validate path, start worker, update model on result."""
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
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_progress(self, event: ProgressEvent) -> None:
        """Update progress dialog from ProgressEvent."""
        if self._progress_dialog is not None:
            self._progress_dialog.update_progress(
                message=event.message,
                value=event.percent if event.total > 0 else None,
                maximum=event.total if event.total > 0 else 100,
            )

    def _on_scan_result(self, result: ScanResult) -> None:
        """Map ScanResult to PipelineRow, update model; then auto-start Parse worker."""
        rows = self._scan_result_to_rows(result)
        self._model.set_rows(group_pipeline_rows(rows))
        if not rows or self._parse_execute is None:
            if self._progress_dialog is not None:
                self._progress_dialog.hide_progress()
            return
        self._start_parse_worker(rows)

    def _scan_result_to_rows(self, result: ScanResult) -> list[PipelineRow]:
        """Convert ScanResult to PipelineRow. Scan phase: path + filename resolution hint."""
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
        """Start Parse worker; on result merge parsed info into rows and set_rows."""
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
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _on_parse_result(self, result: ParseResult) -> None:
        """Merge parsed info into current rows by index; update model."""
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
        """On error, keep model as-is; hide progress dialog."""
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()

    def _on_worker_finished(self, thread: QThread) -> None:
        """Clear _worker_thread only if this thread is the one we're holding."""
        if self._worker_thread is thread:
            self._worker_thread = None

    def on_parse_clicked(self) -> None:
        """Handle parse button click. Phase 4: parse use case."""
        pass

    def on_match_clicked(self) -> None:
        """Run TMDB match worker on current flat pipeline rows."""
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
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_worker_finished(t))
        self._worker_thread = thread

    def _pipeline_row_to_match_file(self, row: PipelineRow) -> MatchFileRow:
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
        merged = [self._match_file_to_pipeline_row(m) for m in result.files]
        self._model.set_rows(group_pipeline_rows(merged))

    def on_build_plan_clicked(self) -> None:
        """Handle build plan button click. Phase 4: plan use case."""
        pass

    def set_rows(self, rows: list[PipelineRow]) -> None:
        """Update pipeline model with file rows (grouped by parsed title for display)."""
        self._model.set_rows(group_pipeline_rows(rows))
