"""OrganizerPresenter: orchestrates OrganizerPage <-> scan/match/plan use cases."""

from PySide6.QtCore import QObject, QThread
from anivault.application.use_cases.scan_library import execute as scan_library_execute
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker


class OrganizerPresenter(QObject):
    """Single orchestration for Organizer page. Validates input, runs workers, updates model."""

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = pipeline_model
        self._worker_thread: QThread | None = None

    def on_scan_clicked(self, path: str) -> None:
        """Handle scan button click. Validate path, start worker, update model on result."""
        path = (path or "").strip()
        if not path:
            return
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=scan_library_execute,
            input_dto=ScanInput(path=path, recursive=True),
            signals=signals,
        )
        signals.result.connect(self._on_scan_result)
        signals.error.connect(self._on_scan_error)
        thread = run_worker(worker)
        thread.finished.connect(self._on_worker_finished)
        self._worker_thread = thread

    def _on_scan_result(self, result: ScanResult) -> None:
        """Map ScanResult to PipelineRow, update model."""
        rows = self._scan_result_to_rows(result)
        self._model.set_rows(rows)

    def _scan_result_to_rows(self, result: ScanResult) -> list[PipelineRow]:
        """Convert ScanResult to PipelineRow. Phase 1+ will enrich."""
        return []

    def _on_scan_error(self, exc: Exception) -> None:
        """On error, keep model as-is. TODO: show error in UI."""
        pass

    def _on_worker_finished(self) -> None:
        self._worker_thread = None

    def on_parse_clicked(self) -> None:
        """Handle parse button click. Phase 4: parse use case."""
        pass

    def on_match_clicked(self) -> None:
        """Handle TMDB match button click. Phase 4: match use case."""
        pass

    def on_build_plan_clicked(self) -> None:
        """Handle build plan button click. Phase 4: plan use case."""
        pass

    def set_rows(self, rows: list[PipelineRow]) -> None:
        """Update pipeline model with rows (e.g. from use case result)."""
        self._model.set_rows(rows)
