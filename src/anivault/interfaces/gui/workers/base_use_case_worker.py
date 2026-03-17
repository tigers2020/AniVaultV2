"""Base worker: QObject + QThread. Runs use case in background, emits signals."""

from threading import Event
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread

from anivault.application.dto.progress import ProgressEvent
from anivault.interfaces.gui.workers.worker_signals import WorkerSignals


class UseCaseWorker(QObject):
    """
    Runs a use case callable in a QThread.
    Emits progress/result/error/cancelled via WorkerSignals.
    """

    def __init__(
        self,
        execute_fn: Callable[[Any, Callable[[ProgressEvent], None], Event], Any],
        input_dto: Any,
        signals: WorkerSignals | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._execute_fn = execute_fn
        self._input_dto = input_dto
        self._signals = signals if signals is not None else WorkerSignals()
        self._cancel = Event()

    def signals(self) -> WorkerSignals:
        return self._signals

    def cancel(self) -> None:
        """Request cancellation. Use case should check cancel token."""
        self._cancel.set()

    def run(self) -> None:
        """Entry point for worker thread. Called when QThread starts."""
        self._signals.started.emit()
        try:
            def progress_cb(event: ProgressEvent) -> None:
                if self._cancel.is_set():
                    return
                self._signals.progress.emit(event)

            if self._cancel.is_set():
                self._signals.cancelled.emit()
                self._signals.finished.emit()
                return

            result = self._execute_fn(self._input_dto, progress_cb, self._cancel)
            if self._cancel.is_set():
                self._signals.cancelled.emit()
            else:
                self._signals.result.emit(result)
        except Exception as e:
            self._signals.error.emit(e)
        finally:
            self._signals.finished.emit()


def run_worker(
    worker: UseCaseWorker,
    on_result: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> QThread:
    """
    Start worker in a new QThread. Returns the thread (caller may hold ref).
    Connect on_result, on_error, on_progress to worker signals.
    """
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    if on_result:
        worker.signals().result.connect(on_result)
    if on_error:
        worker.signals().error.connect(on_error)
    if on_progress:
        worker.signals().progress.connect(on_progress)

    worker.signals().finished.connect(thread.quit)
    thread.start()
    return thread
