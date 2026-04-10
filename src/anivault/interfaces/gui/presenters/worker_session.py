"""worker_session.py

ProgressDialog와 UseCaseWorker를 함께 묶어 QThread를 시작한다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QThread

from anivault.contracts.progress import ProgressEvent
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

logger = logging.getLogger(__name__)


def _disconnect_cancel_on_thread_finished(
    dialog: ProgressDialog,
    cancel_slot: Callable[[], None],
    thread: QThread,
) -> None:
    """스레드 종료 시 취소 시그널 연결을 끊는다(이중 disconnect 방지)."""

    def _disconnect_cancel() -> None:
        try:
            dialog.canceled.disconnect(cancel_slot)
        except (RuntimeError, TypeError, SystemError):
            logger.debug("Progress dialog cancel signal was already disconnected.")

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
    """mark_work_started·show_progress·progress·cancel·run_worker를 한 번에 연결한다.

    Args:
        dialog: 공유 진행 대화상자.
        worker: 백그라운드 유스케이스 워커.
        signals: worker와 동일한 WorkerSignals 인스턴스.
        title: 창 제목.
        message: 라벨 메시지.
        indeterminate: 무한 막대 여부.
        on_progress_with_token: (event, mark_work_started 토큰) 진행 핸들러.
        on_finished: 워커 finished 시그널 슬롯(세션 정리 등).
        on_started: started 직후 추가 작업(예: 모델 지연 반영). show_progress 이후 호출.
        hide_progress_on_cancelled: True면 cancelled 시 hide_progress 연결.

    Returns:
        시작된 QThread.
    """
    token = dialog.mark_work_started()

    def _on_started() -> None:
        dialog.show_progress(title, message, indeterminate)
        if on_started is not None:
            on_started()

    signals.started.connect(_on_started)
    signals.progress.connect(lambda e, t=token: on_progress_with_token(e, t))
    signals.finished.connect(on_finished)
    if hide_progress_on_cancelled:
        signals.cancelled.connect(dialog.hide_progress)
    cancel_slot = worker.cancel
    dialog.canceled.connect(cancel_slot)
    thread = run_worker(worker)
    _disconnect_cancel_on_thread_finished(dialog, cancel_slot, thread)
    return thread
