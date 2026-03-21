"""base_use_case_worker.py

QObject + QThread에서 유스케이스 실행·시그널 보고.

Author: Pom Kim
"""

from collections.abc import Callable
from threading import Event
from typing import Any

from PySide6.QtCore import QObject, QThread

from anivault.application.dto.progress import ProgressEvent
from anivault.interfaces.gui.workers.worker_signals import WorkerSignals


class UseCaseWorker(QObject):
    """유스케이스 callable을 QThread에서 돌리고 WorkerSignals로 알린다."""

    def __init__(
        self,
        execute_fn: Callable[[Any, Callable[[ProgressEvent], None], Event], Any],
        input_dto: Any,
        signals: WorkerSignals | None = None,
        parent: QObject | None = None,
    ) -> None:
        """실행 함수·입력 DTO·시그널 객체를 저장한다.

        Args:
            self: 이 Worker.
            execute_fn: (input_dto, progress_cb, cancel_token) -> result.
            input_dto: 유스케이스 입력.
            signals: 외부에서 공유할 시그널. None이면 새로 생성.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self._execute_fn = execute_fn
        self._input_dto = input_dto
        self._signals = signals if signals is not None else WorkerSignals()
        self._cancel = Event()

    def signals(self) -> WorkerSignals:
        """이 Worker가 사용하는 WorkerSignals를 반환한다.

        Args:
            self: 이 Worker.

        Returns:
            WorkerSignals 인스턴스.
        """
        return self._signals

    def cancel(self) -> None:
        """취소 이벤트를 설정한다. 유스케이스는 토큰을 폴링해야 한다.

        Args:
            self: 이 Worker.

        Returns:
            None.
        """
        self._cancel.set()

    def run(self) -> None:
        """스레드 시작 시 호출되는 진입점. 실행 후 finished를 emit한다.

        Args:
            self: 이 Worker.

        Returns:
            None.
        """
        self._signals.started.emit()
        try:

            def progress_cb(event: ProgressEvent) -> None:
                """취소 중이면 progress를 보내지 않는다.

                Args:
                    event: 진행 이벤트.

                Returns:
                    None.
                """
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
    """새 QThread에서 worker를 시작하고 시그널을 연결한다.

    Args:
        worker: UseCaseWorker 인스턴스.
        on_result: result 시그널 슬롯.
        on_error: error 시그널 슬롯.
        on_progress: progress 시그널 슬롯.

    Returns:
        시작된 QThread(참조 유지 권장).
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
