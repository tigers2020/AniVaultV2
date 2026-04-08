"""OrganizerPresenter worker thread keepalive tests."""

from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class _FakeFinishedSignal:
    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self) -> None:
        for callback in list(self._callbacks):
            callback()


class _FakeThread:
    def __init__(self) -> None:
        self.finished = _FakeFinishedSignal()


def test_register_worker_thread_keeps_multiple_threads_until_finished() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._worker_thread = None  # type: ignore[attr-defined]
    presenter._worker_threads = []  # type: ignore[attr-defined]
    first = _FakeThread()
    second = _FakeThread()

    presenter.register_worker_thread(first)  # type: ignore[arg-type]
    presenter.register_worker_thread(second)  # type: ignore[arg-type]

    assert presenter._worker_threads == [first, second]  # type: ignore[attr-defined]
    assert presenter._worker_thread is second  # type: ignore[attr-defined]

    first.finished.emit()

    assert presenter._worker_threads == [second]  # type: ignore[attr-defined]
    assert presenter._worker_thread is second  # type: ignore[attr-defined]

    second.finished.emit()

    assert presenter._worker_threads == []  # type: ignore[attr-defined]
    assert presenter._worker_thread is None  # type: ignore[attr-defined]
