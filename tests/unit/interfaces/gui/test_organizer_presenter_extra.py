from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.interfaces.gui.models import PipelineRow
from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


def _make_pipeline_row(*, matched: bool = True) -> PipelineRow:
    return PipelineRow(
        original_file="F:/Anime/show01.mkv",
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show" if matched else "",
        tmdb_series_id="1" if matched else "",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="matched" if matched else "parsed",
        poster_url="",
        backdrop_url="",
        target_path="F:/Library/show01.mkv" if matched else "",
    )


def test_finish_worker_session_hides_only_when_requested() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    dialog = MagicMock()

    presenter._finish_worker_session(dialog, hide=False)  # type: ignore[attr-defined]
    presenter._finish_worker_session(dialog, hide=True)  # type: ignore[attr-defined]

    assert dialog.mark_work_finished.call_count == 2
    dialog.hide_progress.assert_called_once()


def test_notify_dry_run_and_should_enable_follow_model_rows() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    calls: list[bool] = []
    presenter._dry_run_enabled_handler = lambda enabled: calls.append(enabled)  # type: ignore[attr-defined]
    presenter._notify_dry_run(True)  # type: ignore[attr-defined]
    presenter._model = SimpleNamespace(flat_rows=lambda: [_make_pipeline_row(matched=True)])  # type: ignore[attr-defined]
    assert presenter._dry_run_should_enable() is True  # type: ignore[attr-defined]
    presenter._model = SimpleNamespace(flat_rows=lambda: [_make_pipeline_row(matched=False)])  # type: ignore[attr-defined]
    assert presenter._dry_run_should_enable() is False  # type: ignore[attr-defined]
    assert calls == [True]


def test_parent_widget_returns_only_qwidget_instances(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)

    class FakeWidget:
        pass

    monkeypatch.setattr(
        "anivault.interfaces.gui.presenters.organizer_presenter.QWidget",
        FakeWidget,
    )
    widget = FakeWidget()
    presenter.parent = lambda: widget  # type: ignore[attr-defined]
    assert presenter._parent_widget() is widget  # type: ignore[attr-defined]
    presenter.parent = lambda: object()  # type: ignore[attr-defined]
    assert presenter._parent_widget() is None  # type: ignore[attr-defined]


def test_register_and_finish_worker_threads_tracks_last_active_thread() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._worker_thread = None  # type: ignore[attr-defined]
    presenter._worker_threads = []  # type: ignore[attr-defined]

    finished_callbacks: list[object] = []
    thread_a = SimpleNamespace(
        finished=SimpleNamespace(connect=lambda cb: finished_callbacks.append(cb))
    )
    thread_b = SimpleNamespace(
        finished=SimpleNamespace(connect=lambda cb: finished_callbacks.append(cb))
    )

    presenter.register_worker_thread(thread_a)  # type: ignore[attr-defined]
    presenter.register_worker_thread(thread_b)  # type: ignore[attr-defined]
    assert presenter._worker_thread is thread_b  # type: ignore[attr-defined]

    presenter._on_worker_finished(thread_b)  # type: ignore[attr-defined]
    assert presenter._worker_thread is thread_a  # type: ignore[attr-defined]

    presenter._on_worker_finished(thread_a)  # type: ignore[attr-defined]
    assert presenter._worker_thread is None  # type: ignore[attr-defined]


def test_on_scan_error_resets_state_and_hides_dialog() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._current_library_root_id = 9  # type: ignore[attr-defined]
    presenter._parse_index_root_id = 7  # type: ignore[attr-defined]
    presenter._progress_dialog = MagicMock()  # type: ignore[attr-defined]

    presenter._on_scan_error(RuntimeError("boom"))  # type: ignore[attr-defined]

    assert presenter._current_library_root_id is None  # type: ignore[attr-defined]
    assert presenter._parse_index_root_id is None  # type: ignore[attr-defined]
    presenter._progress_dialog.hide_progress.assert_called_once()  # type: ignore[attr-defined]
