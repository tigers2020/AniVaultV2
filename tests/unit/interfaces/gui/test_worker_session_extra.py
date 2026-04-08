from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.interfaces.gui.presenters import worker_session as session_module


class _FakeFinishedSignal:
    def __init__(self) -> None:
        self.callback = None

    def connect(self, callback) -> None:
        self.callback = callback


class _FakeThread:
    def __init__(self) -> None:
        self.finished = _FakeFinishedSignal()


def test_disconnect_cancel_on_thread_finished_disconnects_once() -> None:
    dialog = MagicMock()
    thread = _FakeThread()
    cancel_slot = MagicMock()

    session_module._disconnect_cancel_on_thread_finished(dialog, cancel_slot, thread)
    thread.finished.callback()

    dialog.canceled.disconnect.assert_called_once_with(cancel_slot)


def test_run_use_case_worker_with_progress_dialog_wires_signals(monkeypatch) -> None:
    dialog = MagicMock()
    dialog.mark_work_started.return_value = 7
    started_callbacks: list[object] = []
    progress_callbacks: list[object] = []
    finished_callbacks: list[object] = []
    cancelled_callbacks: list[object] = []
    signals = SimpleNamespace(
        started=SimpleNamespace(connect=lambda callback: started_callbacks.append(callback)),
        progress=SimpleNamespace(connect=lambda callback: progress_callbacks.append(callback)),
        finished=SimpleNamespace(connect=lambda callback: finished_callbacks.append(callback)),
        cancelled=SimpleNamespace(connect=lambda callback: cancelled_callbacks.append(callback)),
    )
    worker = SimpleNamespace(cancel=MagicMock())
    thread = _FakeThread()
    monkeypatch.setattr(session_module, "run_worker", lambda incoming: thread)
    on_progress = MagicMock()
    on_finished = MagicMock()
    on_started = MagicMock()

    result = session_module.run_use_case_worker_with_progress_dialog(
        dialog=dialog,
        worker=worker,
        signals=signals,
        title="Scan",
        message="Running",
        indeterminate=True,
        on_progress_with_token=on_progress,
        on_finished=on_finished,
        on_started=on_started,
    )

    started_callbacks[0]()
    progress_callbacks[0]("event")
    finished_callbacks[0]()
    cancelled_callbacks[0]()
    thread.finished.callback()

    assert result is thread
    dialog.show_progress.assert_called_once_with("Scan", "Running", True)
    on_started.assert_called_once()
    on_progress.assert_called_once_with("event", 7)
    on_finished.assert_called_once()
    dialog.canceled.connect.assert_called_once_with(worker.cancel)
    dialog.hide_progress.assert_called_once()
