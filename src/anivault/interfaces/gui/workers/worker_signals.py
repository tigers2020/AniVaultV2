"""worker_signals.py

유스케이스 Worker가 백그라운드 스레드에서 emit하는 시그널 묶음.

Author: Pom Kim
"""

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """진행·결과·오류·취소·종료 시그널. 메인 스레드에서 connect."""

    started = Signal()
    progress = Signal(object)  # ProgressEvent
    result = Signal(object)
    error = Signal(Exception)
    cancelled = Signal()
    finished = Signal()
