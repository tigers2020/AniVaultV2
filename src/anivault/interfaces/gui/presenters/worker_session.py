"""worker_session.py

ProgressDialog·UseCaseWorker 취소 연결 해제 등 워커 세션 소모품.

Author: Pom Kim
"""

from collections.abc import Callable

from PySide6.QtCore import QThread

from anivault.application.dto.progress import ProgressEvent
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker


def disconnect_worker_cancel_on_thread_finished(
    dialog: ProgressDialog,
    worker: UseCaseWorker,
    thread: QThread,
) -> None:
    """스레드 종료 시 ``dialog.canceled``와 ``worker.cancel`` 연결을 끊는다.

    Args:
        dialog: 진행 대화상자.
        worker: 유스케이스 워커.
        thread: 워커를 실행한 QThread.

    Returns:
        None.
    """

    def _disconnect_cancel() -> None:
        """취소 시그널 연결을 끊는다.

        Args:
            없음.

        Returns:
            None.
        """
        dialog.canceled.disconnect(worker.cancel)

    thread.finished.connect(_disconnect_cancel)


def run_use_case_worker_with_progress_dialog(
    *,
    dialog: ProgressDialog,
    worker: UseCaseWorker,
    signals: WorkerSignals,
    title: str,
    message: str,
    indeterminate: bool,
    on_progress_with_token: Callable[[ProgressEvent, int], None],
    on_finished: Callable[[], None],
    on_started: Callable[[], None] | None = None,
    hide_progress_on_cancelled: bool = True,
) -> QThread:
    """ProgressDialog가 있는 워커 실행 보일러플레이트를 공통화한다.

    이 함수는 **lifecycle wiring**(token, progress, cancel, disconnect, finished)만 담당한다.
    result/error 처리·비즈니스 의미 해석은 호출부가 직접 시그널을 연결해야 한다.

    Args:
        dialog: 진행 대화상자.
        worker: 실행할 유스케이스 워커.
        signals: worker가 사용하는 WorkerSignals(호출부에서 공유/연결).
        title: 진행 제목.
        message: 진행 메시지.
        indeterminate: 진행바가 불확정인지 여부.
        on_progress_with_token: (event, token) 진행 콜백.
        on_finished: worker finished 시 호출할 후처리(보통 session 마감).
        on_started: started 시 추가로 호출할 후처리(옵션).
        hide_progress_on_cancelled: cancelled 시 dialog.hide_progress를 호출할지 여부.

    Returns:
        실행된 QThread.
    """
    token = dialog.mark_work_started()

    def _on_started() -> None:
        """워커 started 시 진행 UI를 띄운다."""
        dialog.show_progress(title, message, indeterminate)
        if on_started is not None:
            on_started()

    signals.started.connect(_on_started)
    signals.progress.connect(lambda e, t=token: on_progress_with_token(e, t))
    signals.finished.connect(on_finished)
    if hide_progress_on_cancelled:
        signals.cancelled.connect(dialog.hide_progress)
    dialog.canceled.connect(worker.cancel)

    thread = run_worker(worker)
    disconnect_worker_cancel_on_thread_finished(dialog, worker, thread)
    return thread
