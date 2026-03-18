"""Worker signals bundle. UseCaseWorker emits these from worker thread."""

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """Signals for progress, result, error, cancel. Connect from main thread."""

    started = Signal()
    progress = Signal(object)  # ProgressEvent
    result = Signal(object)
    error = Signal(Exception)
    cancelled = Signal()
    finished = Signal()
