from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.dto.progress import ProgressEvent
from anivault.interfaces.gui.models import PipelineRow
from anivault.interfaces.gui.presenters import organizer_presenter as presenter_module
from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class _FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback, *args, **kwargs) -> None:
        self.callbacks.append(callback)


class _FakeSignals:
    def __init__(self) -> None:
        self.result = _FakeSignal()
        self.error = _FakeSignal()
        self.started = _FakeSignal()
        self.progress = _FakeSignal()
        self.finished = _FakeSignal()
        self.cancelled = _FakeSignal()


class _FakeThread:
    def __init__(self) -> None:
        self.finished = _FakeSignal()


def _candidate() -> TmdbSeriesCandidateDTO:
    return TmdbSeriesCandidateDTO(
        tmdb_id=10,
        name_ko="Show",
        original_name="Show Original",
        first_air_date="2024-01-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
        popularity=1.0,
    )


def test_progress_helpers(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._progress_dialog = MagicMock()  # type: ignore[attr-defined]
    presenter._progress_dialog.is_progress_token_valid.return_value = True  # type: ignore[attr-defined]
    monkeypatch.setattr(
        presenter_module,
        "progress_dialog_value_and_maximum",
        lambda event: (event.current, event.total or 0),
    )

    presenter._on_progress(ProgressEvent(stage="scan", message="Scanning", current=2, total=5, percent=40), 7)  # type: ignore[attr-defined]
    presenter._progress_dialog.is_progress_token_valid.return_value = False  # type: ignore[attr-defined]
    presenter._on_progress(ProgressEvent(stage="scan", message="Ignored", current=1, total=2, percent=50), 8)  # type: ignore[attr-defined]

    presenter._progress_dialog.update_progress.assert_called_once_with(  # type: ignore[attr-defined]
        message="Scanning",
        value=2,
        maximum=5,
    )


def test_dry_run_apply_helper() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._pending_plan = None  # type: ignore[attr-defined]
    presenter._apply_execute = object()  # type: ignore[attr-defined]
    presenter._start_apply_worker = MagicMock()  # type: ignore[attr-defined]
    dlg = MagicMock()
    presenter._on_dry_run_apply_clicked(dlg)  # type: ignore[attr-defined]
    dlg.accept.assert_called_once()
    presenter._start_apply_worker.assert_not_called()  # type: ignore[attr-defined]


def test_start_apply_worker_and_dry_run_clicked_paths(monkeypatch) -> None:
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter.parent = lambda: FakeWidget()  # type: ignore[attr-defined]
    presenter._apply_execute = object()  # type: ignore[attr-defined]
    presenter._on_scan_error = MagicMock()  # type: ignore[attr-defined]
    presenter._on_progress = MagicMock()  # type: ignore[attr-defined]
    presenter._finish_worker_session = MagicMock()  # type: ignore[attr-defined]
    presenter._on_worker_finished = MagicMock()  # type: ignore[attr-defined]
    presenter._on_apply_worker_result = MagicMock()  # type: ignore[attr-defined]
    presenter._progress_dialog = MagicMock()  # type: ignore[attr-defined]
    presenter._progress_dialog.mark_work_started.return_value = 9  # type: ignore[attr-defined]
    warnings: list[str] = []
    infos: list[str] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "warning",
        lambda parent, title, text: warnings.append(text),
    )
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "information",
        lambda parent, title, text: infos.append(text),
    )
    monkeypatch.setattr(presenter_module, "WorkerSignals", _FakeSignals)
    monkeypatch.setattr(
        presenter_module,
        "UseCaseWorker",
        lambda execute_fn, input_dto, signals: SimpleNamespace(cancel=MagicMock(), input_dto=input_dto, signals=signals),
    )
    monkeypatch.setattr(presenter_module, "run_worker", lambda worker: _FakeThread())

    presenter_module.load_all = lambda: {"scan_build": {"source_path": ""}, "path_rules": {"target_root": ""}}
    presenter._start_apply_worker(SimpleNamespace(moves=()))  # type: ignore[attr-defined]
    assert warnings

    presenter_module.load_all = lambda: {"scan_build": {"source_path": "F:/Anime"}, "path_rules": {}}
    presenter._start_apply_worker(SimpleNamespace(moves=("move",)))  # type: ignore[attr-defined]
    assert presenter._worker_thread is not None  # type: ignore[attr-defined]

    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter.parent = lambda: FakeWidget()  # type: ignore[attr-defined]
    presenter._plan_execute = None  # type: ignore[attr-defined]
    presenter.on_dry_run_clicked()  # type: ignore[attr-defined]

    presenter._plan_execute = object()  # type: ignore[attr-defined]
    presenter._model = SimpleNamespace(flat_rows=lambda: ["row"])  # type: ignore[attr-defined]
    presenter._include_companion_subtitles = True  # type: ignore[attr-defined]
    monkeypatch.setattr(presenter_module, "load_all", lambda: {"path_rules": {}})
    monkeypatch.setattr(presenter_module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "empty"))
    presenter.on_dry_run_clicked()  # type: ignore[attr-defined]
    monkeypatch.setattr(presenter_module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "no_matched"))
    presenter.on_dry_run_clicked()  # type: ignore[attr-defined]
    monkeypatch.setattr(presenter_module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "path_rules"))
    presenter.on_dry_run_clicked()  # type: ignore[attr-defined]

    assert len(infos) >= 2


def test_apply_manual_tmdb_candidate_to_model_handles_match_and_empty(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    panel = MagicMock()
    presenter._current_library_root_id = 9  # type: ignore[attr-defined]
    presenter._title_match = object()  # type: ignore[attr-defined]
    presenter._title_groups = object()  # type: ignore[attr-defined]
    presenter._poster_sync = SimpleNamespace(sync_from_files=MagicMock())  # type: ignore[attr-defined]
    presenter._notify_dry_run = MagicMock()  # type: ignore[attr-defined]
    presenter._dry_run_should_enable = MagicMock(return_value=True)  # type: ignore[attr-defined]
    flat_rows = [
        PipelineRow(
            original_file="F:/Anime/a.mkv",
            parsed_title="Show",
            parse_group="show",
            tmdb_korean_title_group="",
            tmdb_series_id="",
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="2024",
            season="1",
            resolution="1080p",
            status="parsed",
            poster_url="",
            backdrop_url="",
            target_path="",
        )
    ]
    presenter._model = SimpleNamespace(flat_rows=lambda: flat_rows, set_rows=MagicMock())  # type: ignore[attr-defined]

    file_rows = [SimpleNamespace(original_file="F:/Anime/a.mkv")]
    monkeypatch.setattr(
        presenter_module,
        "pipeline_row_to_match_file",
        lambda row: file_rows[0],
    )
    apply_calls: list[tuple[list[int], int]] = []
    persist_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        presenter_module,
        "apply_tmdb_candidate_to_file_rows",
        lambda files, indices, chosen: apply_calls.append((indices, chosen.tmdb_id)),
    )
    monkeypatch.setattr(presenter_module, "normalize_path_key", lambda path: f"norm::{path}")
    monkeypatch.setattr(
        presenter_module,
        "persist_manual_tmdb_selection",
        lambda files, indices, chosen, **kwargs: persist_calls.append(kwargs),
    )
    monkeypatch.setattr(
        presenter_module,
        "group_pipeline_rows",
        lambda rows: [SimpleNamespace(members=(SimpleNamespace(original_file="F:/Anime/a.mkv"),))],
    )
    presenter._match_file_to_pipeline_row = lambda match: SimpleNamespace(original_file=match.original_file)  # type: ignore[attr-defined]

    group = SimpleNamespace(members=(SimpleNamespace(original_file="F:/Anime/a.mkv"),))
    presenter._apply_manual_tmdb_candidate_to_model(group, _candidate(), panel)  # type: ignore[attr-defined]

    assert apply_calls == [([0], 10)]
    assert persist_calls and persist_calls[0]["root_id"] == 9
    presenter._poster_sync.sync_from_files.assert_called_once_with(file_rows)  # type: ignore[attr-defined]
    panel.set_pending_selected_group_index.assert_called_once_with(0)
    presenter._model.set_rows.assert_called_once()  # type: ignore[attr-defined]
    presenter._notify_dry_run.assert_called_once_with(True)  # type: ignore[attr-defined]

    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._model = SimpleNamespace(flat_rows=lambda: flat_rows)  # type: ignore[attr-defined]
    monkeypatch.setattr(
        presenter_module,
        "pipeline_row_to_match_file",
        lambda row: SimpleNamespace(original_file="F:/Anime/other.mkv"),
    )
    presenter._apply_manual_tmdb_candidate_to_model(group, _candidate(), panel)  # type: ignore[attr-defined]


def test_run_tmdb_search_worker_validates_and_starts_thread(monkeypatch) -> None:
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter.parent = lambda: FakeWidget()  # type: ignore[attr-defined]
    warnings: list[str] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "warning",
        lambda parent, title, text: warnings.append(text),
    )

    dlg = MagicMock()
    presenter._tmdb_search_execute = None  # type: ignore[attr-defined]
    presenter._run_tmdb_search_worker(dlg, "Show", 2024)  # type: ignore[attr-defined]
    dlg.set_search_busy.assert_called_once_with(False)

    dlg = MagicMock()
    presenter._tmdb_search_execute = object()  # type: ignore[attr-defined]
    presenter._run_tmdb_search_worker(dlg, "   ", 2024)  # type: ignore[attr-defined]
    assert warnings

    thread = _FakeThread()
    worker_box: dict[str, object] = {}

    def _worker_factory(*, execute_fn, input_dto, signals):
        worker = SimpleNamespace(input_dto=input_dto, signals=signals)
        worker_box["worker"] = worker
        return worker

    monkeypatch.setattr(presenter_module, "WorkerSignals", _FakeSignals)
    monkeypatch.setattr(presenter_module, "UseCaseWorker", _worker_factory)
    monkeypatch.setattr(presenter_module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(presenter_module.QTimer, "singleShot", lambda delay, callback: callback())
    monkeypatch.setattr(
        presenter_module,
        "ManualTmdbSearchRelay",
        lambda dlg, presenter: SimpleNamespace(
            on_result=MagicMock(),
            on_error=MagicMock(),
            on_finished=MagicMock(),
        ),
    )

    dlg = MagicMock()
    presenter._run_tmdb_search_worker(dlg, " Show ", "2024")  # type: ignore[attr-defined]

    worker = worker_box["worker"]
    assert worker.input_dto.query == "Show"
    assert worker.input_dto.year is None
    assert presenter._tmdb_worker_keepalive is not None  # type: ignore[attr-defined]
    dlg.set_search_busy.assert_called_with(True)
    assert presenter._worker_thread is thread  # type: ignore[attr-defined]
    presenter._worker_threads = [thread]  # type: ignore[attr-defined]

    for callback in thread.finished.callbacks:
        callback()
    assert presenter._tmdb_worker_keepalive is None  # type: ignore[attr-defined]
