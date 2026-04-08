from unittest.mock import MagicMock

from anivault.interfaces.gui.presenters.worker_session import (
    _disconnect_cancel_on_thread_finished,
)


class _FakeFinishedSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class _FakeThread:
    def __init__(self) -> None:
        self.finished = _FakeFinishedSignal()


def test_worker_session_disconnects_captured_cancel_slot() -> None:
    dialog = MagicMock()
    cancel_slot = MagicMock()
    thread = _FakeThread()

    _disconnect_cancel_on_thread_finished(dialog, cancel_slot, thread)
    thread.finished.callback()

    dialog.canceled.disconnect.assert_called_once_with(cancel_slot)


def test_worker_session_disconnect_ignores_system_error() -> None:
    dialog = MagicMock()
    cancel_slot = MagicMock()
    thread = _FakeThread()
    dialog.canceled.disconnect.side_effect = SystemError("wrapped runtime error")

    _disconnect_cancel_on_thread_finished(dialog, cancel_slot, thread)

    thread.finished.callback()
