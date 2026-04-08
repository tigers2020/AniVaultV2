from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, call

from anivault.application.dto.match_result import MatchInput, MatchResult
from anivault.application.dto.parse import ParseResult
from anivault.application.dto.scan import ScanResult
from anivault.domain.models.parsed_info import ParsedInfo
from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow, PipelineRow
from anivault.interfaces.gui.presenters.organizing import scan_parse_coordinator as module


class _Signal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback, *args, **kwargs) -> None:
        self.callbacks.append(callback)

    def emit(self, *args, **kwargs) -> None:
        for callback in list(self.callbacks):
            callback(*args, **kwargs)


class _Thread:
    def __init__(self) -> None:
        self.finished = _Signal()


class _WorkerSignals:
    def __init__(self) -> None:
        self.result = _Signal()
        self.error = _Signal()
        self.finished = _Signal()


class _Worker:
    def __init__(self, *, execute_fn, input_dto, signals) -> None:
        self.execute_fn = execute_fn
        self.input_dto = input_dto
        self.signals = signals


def _coord(presenter: object) -> module.ScanParseCoordinator:
    coord = module.ScanParseCoordinator.__new__(module.ScanParseCoordinator)
    coord._p = presenter  # type: ignore[attr-defined]
    coord._parse_apply_generation = 0  # type: ignore[attr-defined]
    coord._parse_snapshot = None  # type: ignore[attr-defined]
    coord._pending_cached_hydrate = {}  # type: ignore[attr-defined]
    coord._pending_cached_missing_fill = {}  # type: ignore[attr-defined]
    return coord


def _row(path: str) -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="",
        parse_group="",
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="",
        resolution="FHD",
        status="스캔됨",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode="",
    )


def test_execute_worker_helpers_handle_cancel_and_hydrate() -> None:
    sync_calls: list[int] = []
    token = MagicMock()
    token.is_set.return_value = False
    assert (
        module._execute_title_groups_sync_worker(7, None, token, sync_fn=sync_calls.append) is None
    )
    assert sync_calls == [7]

    token.is_set.return_value = True
    result = module._execute_cached_tmdb_hydrate_worker(
        MatchInput(),
        None,
        token,
        hydrate_fn=lambda dto: MatchResult(files=()),
    )
    assert result == MatchResult(files=())


def test_scan_path_is_usable_directory_covers_success_and_errors(monkeypatch) -> None:
    presenter = SimpleNamespace(parent=lambda: None)
    coord = _coord(presenter)
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        coord, "_warn_scan_path", lambda title, message: warnings.append((title, message))
    )
    monkeypatch.setattr(module.Path, "is_dir", lambda self: True)
    assert coord._scan_path_is_usable_directory("F:/Anime") is True

    monkeypatch.setattr(module.Path, "is_dir", lambda self: (_ for _ in ()).throw(OSError("bad")))
    assert coord._scan_path_is_usable_directory("F:/Anime") is False
    monkeypatch.setattr(module.Path, "is_dir", lambda self: False)
    assert coord._scan_path_is_usable_directory("F:/Anime") is False
    assert warnings[0][0] == "스캔 경로 오류"
    assert warnings[1][0] == "스캔 경로 없음"


def test_on_scan_clicked_handles_blank_invalid_and_no_execute(monkeypatch) -> None:
    presenter = SimpleNamespace(_notify_dry_run=MagicMock(), _scan_execute=None)
    coord = _coord(presenter)
    warned: list[str] = []
    monkeypatch.setattr(coord, "_warn_scan_path", lambda title, body: warned.append(title))
    coord.on_scan_clicked("   ")
    monkeypatch.setattr(coord, "_scan_path_is_usable_directory", lambda path: False)
    coord.on_scan_clicked("F:/Anime")
    monkeypatch.setattr(coord, "_scan_path_is_usable_directory", lambda path: True)
    coord.on_scan_clicked("F:/Anime")

    assert warned == ["스캔 경로 없음"]
    presenter._notify_dry_run.assert_called_once_with(False)


def test_on_scan_clicked_starts_worker(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    presenter = SimpleNamespace(
        _notify_dry_run=MagicMock(),
        _scan_execute=lambda *args: None,
        _on_scan_error=MagicMock(),
        _progress_dialog=None,
        register_worker_thread=MagicMock(),
        _current_library_root_id=1,
        _scan_progress_handoff_done=True,
        _exclude_subtitles_with_paired_video=False,
    )
    coord = _coord(presenter)
    monkeypatch.setattr(coord, "_scan_path_is_usable_directory", lambda path: True)

    coord.on_scan_clicked("F:/Anime")

    presenter.register_worker_thread.assert_called_once_with(thread)


def test_on_scan_thread_finished_only_when_handoff_not_done() -> None:
    presenter = SimpleNamespace(
        _scan_progress_handoff_done=False, _finish_worker_session=MagicMock()
    )
    coord = _coord(presenter)
    dialog = MagicMock()

    coord._on_scan_thread_finished(dialog)
    presenter._scan_progress_handoff_done = True
    coord._on_scan_thread_finished(dialog)

    presenter._finish_worker_session.assert_called_once_with(dialog, hide=False)


def test_on_progress_updates_dialog_when_token_valid() -> None:
    dialog = MagicMock()
    dialog.is_progress_token_valid.return_value = True
    coord = _coord(SimpleNamespace(_progress_dialog=dialog))

    coord._on_progress(SimpleNamespace(message="msg", current=1, total=2), 5)

    dialog.update_progress.assert_called_once()


def test_on_scan_result_sets_rows_or_starts_parse(monkeypatch) -> None:
    presenter = SimpleNamespace(
        _model=SimpleNamespace(set_rows=MagicMock()),
        _parse_execute=None,
        _progress_dialog=MagicMock(),
        _finish_worker_session=MagicMock(),
        _scan_progress_handoff_done=False,
        _current_library_root_id=None,
    )
    coord = _coord(presenter)
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: ["group"])
    monkeypatch.setattr(coord, "_scan_result_to_rows", lambda result: [])

    coord._on_scan_result(ScanResult(paths=[], resolutions=[], index_root_id=3))

    presenter._model.set_rows.assert_called_once_with(["group"])
    presenter._finish_worker_session.assert_called_once()

    started: list[object] = []
    monkeypatch.setattr(coord, "_scan_result_to_rows", lambda result: [_row("a.mkv")])
    monkeypatch.setattr(
        coord,
        "_start_parse_worker",
        lambda rows, merged, index_root_id: started.append((rows, merged, index_root_id)),
    )
    presenter._parse_execute = object()
    coord._on_scan_result(ScanResult(paths=["a.mkv"], resolutions=["FHD"], index_root_id=4))

    assert started and started[0][2] == 4


def test_scan_result_to_rows_maps_paths_and_resolutions() -> None:
    coord = _coord(SimpleNamespace())

    rows = coord._scan_result_to_rows(
        ScanResult(paths=["a.mkv", "b.mkv"], resolutions=["FHD"], index_root_id=1)
    )

    assert [row.resolution for row in rows] == ["FHD", ""]
    assert all(row.status == "스캔됨" for row in rows)


def test_start_parse_worker_handles_missing_execute_and_starts_worker(monkeypatch) -> None:
    coord = _coord(SimpleNamespace(_parse_execute=None))
    coord._start_parse_worker([], [])

    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    presenter = SimpleNamespace(
        _parse_execute=lambda *args: None,
        _parse_index_root_id=None,
        _progress_dialog=None,
        _on_scan_error=MagicMock(),
        register_worker_thread=MagicMock(),
        _scan_progress_handoff_done=False,
    )
    coord = _coord(presenter)

    coord._start_parse_worker([_row("a.mkv")], [PipelineGroupRow((_row("a.mkv"),))], 9)

    assert presenter._parse_index_root_id == 9
    presenter.register_worker_thread.assert_called_once_with(thread)


def test_on_parse_result_ignores_stale_generation_and_merges_rows(monkeypatch) -> None:
    applied: list[object] = []
    model = SimpleNamespace(flat_rows=lambda: [_row("a.mkv")])
    presenter = SimpleNamespace(
        _model=model, _parse_index_root_id=5, _sync_title_groups_execute=None
    )
    coord = _coord(presenter)
    coord._parse_apply_generation = 2  # type: ignore[attr-defined]
    monkeypatch.setattr(
        coord,
        "_apply_parse_result_rows_after_optional_hydrate",
        lambda *args, **kwargs: applied.append((args, kwargs)),
    )

    coord._on_parse_result(ParseResult(parsed=[]), 1)
    assert applied == []

    coord._parse_snapshot = (2, [_row("a.mkv")])  # type: ignore[attr-defined]
    coord._on_parse_result(
        ParseResult(
            parsed=[
                ParsedInfo(
                    title="Show",
                    parse_group="Group",
                    year="2024",
                    season="1",
                    episode="2",
                    resolution="UHD",
                )
            ]
        ),
        2,
    )

    assert applied
    merged_rows = applied[0][0][1]
    assert merged_rows[0].parsed_title == "Show"
    assert merged_rows[0].resolution == "UHD"


def test_apply_parse_result_rows_after_optional_hydrate_tracks_pending_job(monkeypatch) -> None:
    applied: list[object] = []
    presenter = SimpleNamespace(
        _cached_tmdb_hydrate_execute=object(),
        _cached_tmdb_missing_fill_execute=object(),
    )
    coord = _coord(presenter)
    monkeypatch.setattr(
        coord,
        "_apply_parse_result_groups_chunked",
        lambda *args, **kwargs: applied.append((args, kwargs)),
    )
    monkeypatch.setattr(
        module,
        "pipeline_row_to_match_file",
        lambda row: SimpleNamespace(original_file=row.original_file),
    )
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: ["group"])

    coord._apply_parse_result_rows_after_optional_hydrate(
        MagicMock(),
        [_row("a.mkv")],
        session_gen=3,
        root_for_sync=7,
        sync_fn=None,
    )

    assert 3 in coord._pending_cached_hydrate  # type: ignore[attr-defined]
    assert 3 in coord._pending_cached_missing_fill  # type: ignore[attr-defined]
    assert applied


def test_run_pending_cached_tmdb_hydrate_returns_false_when_no_pending() -> None:
    presenter = SimpleNamespace(_cached_tmdb_hydrate_execute=lambda dto: None)
    coord = _coord(presenter)
    coord._parse_apply_generation = 1  # type: ignore[attr-defined]
    assert coord._run_pending_cached_tmdb_hydrate(1) is False


def test_run_pending_cached_tmdb_missing_fill_returns_false_when_no_pending() -> None:
    presenter = SimpleNamespace(_cached_tmdb_missing_fill_execute=lambda *a: None)
    coord = _coord(presenter)
    coord._parse_apply_generation = 1  # type: ignore[attr-defined]
    assert coord._run_pending_cached_tmdb_missing_fill(1) is False


def test_run_pending_cached_tmdb_hydrate_starts_worker(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    presenter = SimpleNamespace(
        _cached_tmdb_hydrate_execute=lambda dto: MatchResult(files=()),
        register_worker_thread=MagicMock(),
    )
    coord = _coord(presenter)
    coord._parse_apply_generation = 2  # type: ignore[attr-defined]
    coord._pending_cached_hydrate[2] = (MagicMock(), MatchInput())  # type: ignore[attr-defined]

    assert coord._run_pending_cached_tmdb_hydrate(2) is True

    presenter.register_worker_thread.assert_called_once_with(thread)


def test_run_pending_cached_tmdb_missing_fill_starts_worker(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    presenter = SimpleNamespace(
        _cached_tmdb_missing_fill_execute=lambda dto, progress, token: MatchResult(files=()),
        register_worker_thread=MagicMock(),
    )
    coord = _coord(presenter)
    coord._parse_apply_generation = 2  # type: ignore[attr-defined]
    coord._pending_cached_missing_fill[2] = (MagicMock(), MatchInput())  # type: ignore[attr-defined]

    assert coord._run_pending_cached_tmdb_missing_fill(2) is True

    presenter.register_worker_thread.assert_called_once_with(thread)


def test_on_cached_tmdb_hydrate_result_applies_grouped_rows_when_current(monkeypatch) -> None:
    applied: list[object] = []
    presenter = SimpleNamespace(
        _match_file_to_pipeline_row=lambda file: _row(file.original_file),
        _current_library_root_id=1,
        _cached_tmdb_missing_fill_execute=None,
    )
    coord = _coord(presenter)
    coord._parse_apply_generation = 1  # type: ignore[attr-defined]
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: ["group"])

    def capture_apply(*args, **kwargs) -> None:
        assert 1 in coord._pending_cached_missing_fill  # type: ignore[attr-defined]
        applied.append((args, kwargs))

    monkeypatch.setattr(coord, "_apply_parse_result_groups_chunked", capture_apply)

    coord._on_cached_tmdb_hydrate_result(
        MatchResult(files=(SimpleNamespace(original_file="a.mkv"),)), MagicMock(), 1
    )

    assert applied


def test_after_parse_result_groups_applied_syncs_panel_and_optionally_runs_workers(
    monkeypatch,
) -> None:
    panel = SimpleNamespace(sync_views_from_model=MagicMock())
    presenter = SimpleNamespace(
        _pipeline_panel=panel,
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
    )
    coord = _coord(presenter)
    monkeypatch.setattr(coord, "_run_pending_cached_tmdb_hydrate", MagicMock(return_value=False))
    monkeypatch.setattr(
        coord, "_run_pending_cached_tmdb_missing_fill", MagicMock(return_value=False)
    )
    monkeypatch.setattr(coord, "_run_title_groups_sync_worker", MagicMock())

    coord._after_parse_result_groups_applied(
        session_gen=4, root_for_sync=8, sync_fn=lambda root: None
    )

    panel.sync_views_from_model.assert_called_once()
    assert presenter._notify_dry_run.call_args_list == [call(False), call(True)]
    coord._run_pending_cached_tmdb_hydrate.assert_called_once_with(4)
    coord._run_pending_cached_tmdb_missing_fill.assert_called_once_with(4)
    coord._run_title_groups_sync_worker.assert_called_once()


def test_after_parse_result_groups_applied_skips_dry_run_enable_when_followup_starts(
    monkeypatch,
) -> None:
    panel = SimpleNamespace(sync_views_from_model=MagicMock())
    presenter = SimpleNamespace(
        _pipeline_panel=panel,
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
    )
    coord = _coord(presenter)
    monkeypatch.setattr(coord, "_run_pending_cached_tmdb_hydrate", MagicMock(return_value=True))
    monkeypatch.setattr(
        coord, "_run_pending_cached_tmdb_missing_fill", MagicMock(return_value=False)
    )
    monkeypatch.setattr(coord, "_run_title_groups_sync_worker", MagicMock())
    coord._pending_cached_hydrate[5] = (MagicMock(), MatchInput())  # type: ignore[attr-defined]

    coord._after_parse_result_groups_applied(session_gen=5, root_for_sync=None, sync_fn=None)

    presenter._notify_dry_run.assert_called_once_with(False)


def test_run_title_groups_sync_worker_starts_background_job(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    presenter = SimpleNamespace(register_worker_thread=MagicMock())
    coord = _coord(presenter)

    coord._run_title_groups_sync_worker(7, lambda root: None)

    presenter.register_worker_thread.assert_called_once_with(thread)


def test_schedule_parse_result_chunk_work_processes_all_chunks(monkeypatch) -> None:
    model = SimpleNamespace(append_row_groups=MagicMock())
    coord = _coord(SimpleNamespace())
    finished: list[object] = []
    monkeypatch.setattr(module.QTimer, "singleShot", lambda delay, callback: callback())
    monkeypatch.setattr(
        coord, "_after_parse_result_groups_applied", lambda **kwargs: finished.append(kwargs)
    )
    grouped = [PipelineGroupRow((_row("a.mkv"),)), PipelineGroupRow((_row("b.mkv"),))]

    coord._schedule_parse_result_chunk_work(
        model,
        grouped,
        session_gen=0,
        chunk_sz=1,
        n=2,
        idx_ref=[0],
        root_for_sync=None,
        sync_fn=None,
    )

    assert model.append_row_groups.call_count == 2
    assert finished


def test_apply_parse_result_groups_chunked_clears_model_and_schedules(monkeypatch) -> None:
    model = SimpleNamespace(clear_with_reset=MagicMock())
    coord = _coord(SimpleNamespace())
    scheduled: list[object] = []
    monkeypatch.setattr(
        coord,
        "_schedule_parse_result_chunk_work",
        lambda *args, **kwargs: scheduled.append((args, kwargs)),
    )

    coord._apply_parse_result_groups_chunked(
        model,
        [PipelineGroupRow((_row("a.mkv"),))],
        session_gen=1,
        root_for_sync=None,
        sync_fn=None,
    )

    model.clear_with_reset.assert_called_once()
    assert scheduled
