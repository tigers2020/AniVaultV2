from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

from anivault.application.dto.match_result import MatchFileRow, MatchResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.interfaces.gui.models.ui_rows import PipelineGroupRow, PipelineRow
from anivault.interfaces.gui.presenters.organizing import match_coordinator as module
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel


class _Signal:
    def __init__(self) -> None:
        self.callbacks: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        self.callbacks.append(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in tuple(self.callbacks):
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
        self.cancel = MagicMock()


class _Panel:
    def __init__(self, selected_index: int = 0) -> None:
        self._selected_index = selected_index
        self.pending_index = None

    def selected_group_index(self) -> int:
        return self._selected_index

    def set_pending_selected_group_index(self, index: int) -> None:
        self.pending_index = index


def _row(original: str, *, parsed: str = "Parsed", title: str = "") -> PipelineRow:
    return PipelineRow(
        original_file=original,
        parsed_title=parsed,
        parse_group=parsed,
        tmdb_korean_title_group=title,
        tmdb_series_id="1" if title else "",
        tmdb_poster_path="/poster.jpg" if title else "",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="FHD",
        status="ready",
        poster_url="http://poster",
        backdrop_url="",
        target_path="",
        episode="1",
    )


def _file_row(
    original: str, *, series_id: str = "", poster_path: str = "", poster_url: str = ""
) -> MatchFileRow:
    return MatchFileRow(
        original_file=original,
        parsed_title="Parsed",
        parse_group="Parsed",
        tmdb_korean_title_group="Title",
        tmdb_series_id=series_id,
        tmdb_poster_path=poster_path,
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="FHD",
        status="ready",
        poster_url=poster_url,
        backdrop_url="",
        target_path="",
        episode="1",
    )


def _candidate(tmdb_id: int = 7) -> TmdbSeriesCandidateDTO:
    return TmdbSeriesCandidateDTO(
        tmdb_id=tmdb_id,
        name_ko="Frieren",
        original_name="Sousou no Frieren",
        first_air_date="2023-09-29",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )


def _coordinator(presenter: object) -> module.MatchCoordinator:
    coord = module.MatchCoordinator.__new__(module.MatchCoordinator)
    coord._p = presenter  # type: ignore[attr-defined]
    return coord


def test_on_progress_updates_dialog_when_token_is_valid() -> None:
    dialog = MagicMock()
    dialog.is_progress_token_valid.return_value = True
    presenter = SimpleNamespace(_progress_dialog=dialog)
    coord = _coordinator(presenter)

    coord._on_progress(
        ProgressEvent(stage="match", current=1, total=2, message="msg", percent=50),
        3,
    )

    dialog.update_progress.assert_called_once()


def test_on_match_clicked_warns_when_match_execute_missing(monkeypatch) -> None:
    warnings: list[tuple[object, str, str]] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox,
        "warning",
        lambda parent, title, body: warnings.append((parent, title, body)),
    )
    presenter = SimpleNamespace(_match_execute=None, parent=lambda: object())
    coord = _coordinator(presenter)

    coord.on_match_clicked()

    assert warnings and warnings[0][1] == "TMDB API 키 없음"


def test_on_match_clicked_warns_when_no_rows(monkeypatch) -> None:
    infos: list[tuple[object, str, str]] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox,
        "information",
        lambda parent, title, body: infos.append((parent, title, body)),
    )
    presenter = SimpleNamespace(
        _match_execute=object(),
        _notify_dry_run=MagicMock(),
        _model=SimpleNamespace(flat_rows=lambda: []),
        parent=lambda: object(),
    )
    coord = _coordinator(presenter)

    coord.on_match_clicked()

    presenter._notify_dry_run.assert_called_once_with(False)
    assert infos and infos[0][1] == "매칭할 항목 없음"


def test_on_match_clicked_starts_worker_without_progress_dialog(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(
        module, "pipeline_row_to_match_file", lambda row: _file_row(row.original_file)
    )
    presenter = SimpleNamespace(
        _match_execute=lambda *args: None,
        _notify_dry_run=MagicMock(),
        _model=SimpleNamespace(flat_rows=lambda: [_row("a.mkv")]),
        _current_library_root_id=5,
        _on_scan_error=MagicMock(),
        _progress_dialog=None,
        _on_worker_finished=MagicMock(),
        _worker_thread=None,
        parent=lambda: None,
    )
    coord = _coordinator(presenter)

    coord.on_match_clicked()
    thread.finished.emit()

    assert presenter._worker_thread is thread
    presenter._on_worker_finished.assert_called_once_with(thread)


def test_match_file_to_pipeline_row_prefers_local_poster_path(monkeypatch) -> None:
    title_match = SimpleNamespace(get_poster_local_path=lambda *args: "C:/poster.jpg")
    presenter = SimpleNamespace(_title_match=title_match)
    coord = _coordinator(presenter)
    monkeypatch.setattr(
        module, "resolve_final_poster_display_source", lambda local, remote: local or remote
    )

    row = coord._match_file_to_pipeline_row(
        _file_row("a.mkv", series_id="7", poster_path="/poster.jpg", poster_url="http://remote")
    )

    assert row.poster_url == "C:/poster.jpg"


def test_match_file_to_pipeline_row_falls_back_when_poster_lookup_errors(monkeypatch) -> None:
    def _raise(*_args: object) -> None:
        raise ValueError("bad")

    title_match = SimpleNamespace(get_poster_local_path=_raise)
    presenter = SimpleNamespace(_title_match=title_match)
    coord = _coordinator(presenter)
    monkeypatch.setattr(
        module, "resolve_final_poster_display_source", lambda local, remote: local or remote
    )

    row = coord._match_file_to_pipeline_row(
        _file_row("a.mkv", series_id="7", poster_path="/poster.jpg", poster_url="http://remote")
    )

    assert row.poster_url == "http://remote"


def test_on_match_result_uses_compatible_update_when_possible(monkeypatch) -> None:
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: ["group"])
    presenter = SimpleNamespace(
        _model=SimpleNamespace(update_rows_if_compatible=lambda groups: True, set_rows=MagicMock()),
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
    )
    coord = _coordinator(presenter)
    monkeypatch.setattr(coord, "_match_file_to_pipeline_row", lambda file: _row(file.original_file))

    coord._on_match_result(MatchResult(files=(_file_row("a.mkv"),)))

    presenter._model.set_rows.assert_not_called()
    presenter._notify_dry_run.assert_called_once_with(True)


def test_on_match_result_resets_model_when_update_is_incompatible(monkeypatch) -> None:
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: ["group"])
    set_rows = MagicMock()
    presenter = SimpleNamespace(
        _model=SimpleNamespace(update_rows_if_compatible=lambda groups: False, set_rows=set_rows),
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: False,
    )
    coord = _coordinator(presenter)
    monkeypatch.setattr(coord, "_match_file_to_pipeline_row", lambda file: _row(file.original_file))

    coord._on_match_result(MatchResult(files=(_file_row("a.mkv"),)))

    set_rows.assert_called_once_with(["group"])


def test_selected_pipeline_group_index_or_warn_paths(monkeypatch) -> None:
    infos: list[tuple[object, str, str]] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox,
        "information",
        lambda parent, title, body: infos.append((parent, title, body)),
    )
    presenter = SimpleNamespace(_parent_widget=lambda: object())
    coord = _coordinator(presenter)
    rows = [PipelineGroupRow((_row("a.mkv"),))]

    assert (
        coord._selected_pipeline_group_index_or_warn(cast(PipelineResultPanel, _Panel(0)), rows)
        == 0
    )
    assert (
        coord._selected_pipeline_group_index_or_warn(cast(PipelineResultPanel, _Panel(-1)), rows)
        is None
    )
    assert infos and infos[0][1] == "선택 없음"


def test_apply_manual_tmdb_candidate_to_model_updates_rows_and_panel(monkeypatch) -> None:
    stub_panel = _Panel()
    panel = cast(PipelineResultPanel, stub_panel)
    original_group = PipelineGroupRow((_row("a.mkv"),))
    files = [_file_row("a.mkv")]
    merged_groups = [PipelineGroupRow((_row("a.mkv", title="Frieren"),))]
    model = SimpleNamespace(
        flat_rows=lambda: [_row("a.mkv")],
        update_rows_if_compatible=lambda groups: False,
        set_rows=MagicMock(),
    )
    poster_sync = SimpleNamespace(sync_from_files=MagicMock())
    presenter = SimpleNamespace(
        _model=model,
        _current_library_root_id=4,
        _title_match=object(),
        _title_groups=object(),
        _poster_sync=poster_sync,
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
    )
    coord = _coordinator(presenter)
    monkeypatch.setattr(module, "pipeline_row_to_match_file", lambda row: files[0])
    monkeypatch.setattr(
        module,
        "apply_tmdb_candidate_to_file_rows",
        lambda file_rows, indices, chosen: file_rows.__setitem__(
            0, _file_row("a.mkv", series_id=str(chosen.tmdb_id), poster_url="updated")
        ),
    )
    monkeypatch.setattr(module, "persist_manual_tmdb_selection", MagicMock())
    monkeypatch.setattr(module, "group_pipeline_rows", lambda rows: merged_groups)
    monkeypatch.setattr(
        coord, "_match_file_to_pipeline_row", lambda file: _row(file.original_file, title="Frieren")
    )

    coord._apply_manual_tmdb_candidate_to_model(original_group, _candidate(9), panel)

    assert stub_panel.pending_index == 0
    poster_sync.sync_from_files.assert_called_once()
    model.set_rows.assert_called_once_with(merged_groups)
    presenter._notify_dry_run.assert_called_once_with(True)


def test_on_manual_tmdb_match_clicked_control_flow(monkeypatch) -> None:
    dialog = MagicMock()
    dialog.exec.return_value = module.QDialog.DialogCode.Accepted
    dialog.selected_candidate.return_value = _candidate(8)
    dialog.search_requested = _Signal()
    panel = _Panel(0)
    rows = [PipelineGroupRow((_row("a.mkv"),))]
    presenter = SimpleNamespace(
        _tmdb_search_execute=None,
        _pipeline_panel=panel,
        _model=SimpleNamespace(rows=lambda: rows),
        _parent_widget=lambda: None,
    )
    coord = _coordinator(presenter)
    warn_mock = MagicMock()
    monkeypatch.setattr(coord, "_warn_missing_tmdb_api_key", warn_mock)
    coord.on_manual_tmdb_match_clicked()
    warn_mock.assert_called_once()

    presenter._tmdb_search_execute = object()
    presenter._pipeline_panel = None
    coord.on_manual_tmdb_match_clicked()

    presenter._pipeline_panel = panel
    monkeypatch.setattr(module, "TmdbManualMatchDialog", lambda parent, default_query: dialog)
    monkeypatch.setattr(
        coord, "_selected_pipeline_group_index_or_warn", lambda panel_arg, rows_arg: 0
    )
    applied: list[tuple[PipelineGroupRow, TmdbSeriesCandidateDTO, _Panel]] = []
    monkeypatch.setattr(
        coord,
        "_apply_manual_tmdb_candidate_to_model",
        lambda group, chosen, panel_arg: applied.append((group, chosen, panel_arg)),
    )

    coord.on_manual_tmdb_match_clicked()

    assert applied and applied[0][1].tmdb_id == 8


def test_run_tmdb_search_worker_paths(monkeypatch) -> None:
    thread = _Thread()
    warnings: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "warning", lambda parent, title, body: warnings.append(title)
    )
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(
        module,
        "ManualTmdbSearchRelay",
        lambda dlg, presenter: SimpleNamespace(
            on_result=lambda result: None, on_error=lambda exc: None, on_finished=lambda: None
        ),
    )
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(module.QTimer, "singleShot", lambda delay, callback: callback())
    presenter = SimpleNamespace(
        _tmdb_search_execute=None,
        _tmdb_worker_keepalive=None,
        _on_worker_finished=MagicMock(),
        _worker_thread=None,
        parent=lambda: object(),
    )
    coord = _coordinator(presenter)
    dlg = MagicMock()

    coord._run_tmdb_search_worker(dlg, "query", None)
    presenter._tmdb_search_execute = object()
    coord._run_tmdb_search_worker(dlg, "   ", None)
    presenter._tmdb_search_execute = lambda *args: None
    coord._run_tmdb_search_worker(dlg, "Frieren", "2024")
    thread.finished.emit()

    assert "검색어 없음" in warnings
    presenter._on_worker_finished.assert_called_once_with(thread)
    assert presenter._worker_thread is thread
