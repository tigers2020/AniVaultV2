"""worker_session.py

ProgressDialog·UseCaseWorker 취소 연결 해제 등 워커 세션 소모품.

Author: Pom Kim
"""

from PySide6.QtCore import QThread

from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.workers import UseCaseWorker


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
