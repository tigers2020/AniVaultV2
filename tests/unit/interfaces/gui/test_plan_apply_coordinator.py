from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.application.dto.plan import ApplyResult, PlanMovePreviewMeta, PlanResult
from anivault.domain.models.file_operation import FileOperation, OperationType
from anivault.interfaces.gui.presenters.organizing import plan_apply_coordinator as module


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


def _plan() -> PlanResult:
    return PlanResult(
        moves=(FileOperation(OperationType.MOVE, "a", "b"),),
        move_preview=(PlanMovePreviewMeta("tmdb:1", "Frieren", "1080p"),),
        organize_plan_id=7,
        organize_item_ids=(9,),
    )


def _coord(presenter: object) -> module.PlanApplyCoordinator:
    coord = module.PlanApplyCoordinator.__new__(module.PlanApplyCoordinator)
    coord._p = presenter  # type: ignore[attr-defined]
    return coord


def test_on_progress_updates_dialog_when_token_valid() -> None:
    dialog = MagicMock()
    dialog.is_progress_token_valid.return_value = True
    coord = _coord(SimpleNamespace(_progress_dialog=dialog))

    coord._on_progress(SimpleNamespace(message="msg", current=1, total=2), 5)

    dialog.update_progress.assert_called_once()


def test_on_dry_run_clicked_handles_validation_errors(monkeypatch) -> None:
    infos: list[str] = []
    warnings: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "information", lambda parent, title, body: infos.append(title)
    )
    monkeypatch.setattr(
        module.QMessageBox, "warning", lambda parent, title, body: warnings.append(title)
    )
    monkeypatch.setattr(module, "load_all", lambda: {"path_rules": {}})
    presenter = SimpleNamespace(
        _plan_execute=object(),
        _model=SimpleNamespace(flat_rows=lambda: []),
        _include_companion_subtitles=True,
        _current_library_root_id=None,
        parent=lambda: object(),
    )
    coord = _coord(presenter)

    monkeypatch.setattr(
        module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "empty")
    )
    coord.on_dry_run_clicked()
    monkeypatch.setattr(
        module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "no_matched")
    )
    coord.on_dry_run_clicked()
    monkeypatch.setattr(
        module, "try_build_plan_input_from_settings", lambda *args, **kwargs: (None, "path_rules")
    )
    coord.on_dry_run_clicked()

    assert infos == ["항목 없음", "TMDB 매칭 없음"]
    assert warnings == ["경로 규칙"]


def test_on_dry_run_clicked_starts_worker(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(module, "load_all", lambda: {"path_rules": {}})
    monkeypatch.setattr(
        module,
        "try_build_plan_input_from_settings",
        lambda *args, **kwargs: (SimpleNamespace(), None),
    )
    presenter = SimpleNamespace(
        _plan_execute=lambda *args: None,
        _model=SimpleNamespace(flat_rows=lambda: [object()]),
        _include_companion_subtitles=True,
        _current_library_root_id=1,
        _on_scan_error=MagicMock(),
        _progress_dialog=None,
        _on_worker_finished=MagicMock(),
        _worker_thread=None,
        parent=lambda: None,
    )
    coord = _coord(presenter)

    coord.on_dry_run_clicked()
    thread.finished.emit()

    presenter._on_worker_finished.assert_called_once_with(thread)
    assert presenter._worker_thread is thread


def test_on_plan_worker_result_handles_error_and_empty_moves(monkeypatch) -> None:
    infos: list[str] = []
    warnings: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "information", lambda parent, title, body: infos.append(title)
    )
    monkeypatch.setattr(
        module.QMessageBox, "warning", lambda parent, title, body: warnings.append(title)
    )
    presenter = SimpleNamespace(
        _progress_dialog=MagicMock(),
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
        parent=lambda: object(),
    )
    coord = _coord(presenter)

    coord._on_plan_worker_result(PlanResult(error="bad"))
    coord._on_plan_worker_result(PlanResult(moves=()))

    assert warnings == ["플랜 오류"]
    assert infos == ["Dry Run"]


def test_on_plan_worker_result_opens_dialog_and_resets_pending_plan(monkeypatch) -> None:
    dialog = MagicMock()
    dialog.apply_requested = _Signal()
    calls: list[tuple[object, object, object]] = []

    def _dialog_factory(moves, move_preview, parent=None):
        calls.append((moves, move_preview, parent))
        return dialog

    monkeypatch.setattr(module, "DryRunDialog", _dialog_factory)
    presenter = SimpleNamespace(_progress_dialog=None, _pending_plan=None, parent=lambda: None)
    coord = _coord(presenter)

    coord._on_plan_worker_result(_plan())

    dialog.exec.assert_called_once()
    assert calls == [(_plan().moves, _plan().move_preview, None)]
    assert presenter._pending_plan is None


def test_on_dry_run_apply_clicked_warns_when_apply_execute_missing(monkeypatch) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "warning", lambda parent, title, body: warnings.append(title)
    )
    presenter = SimpleNamespace(_pending_plan=_plan(), _apply_execute=None, parent=lambda: object())
    coord = _coord(presenter)
    dlg = MagicMock()

    coord._on_dry_run_apply_clicked(dlg)

    dlg.accept.assert_called_once()
    assert warnings == ["실제 이동 불가"]


def test_on_dry_run_apply_clicked_schedules_apply_worker(monkeypatch) -> None:
    scheduled: list[object] = []
    monkeypatch.setattr(
        module.QTimer, "singleShot", lambda delay, callback: scheduled.append(callback)
    )
    presenter = SimpleNamespace(_pending_plan=_plan(), _apply_execute=object(), parent=lambda: None)
    coord = _coord(presenter)
    monkeypatch.setattr(coord, "_start_apply_worker", lambda plan: scheduled.append(plan))
    dlg = MagicMock()

    coord._on_dry_run_apply_clicked(dlg)
    scheduled[0]()

    assert scheduled[1] == presenter._pending_plan


def test_start_apply_worker_warns_without_log_root(monkeypatch) -> None:
    warnings: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "warning", lambda parent, title, body: warnings.append(title)
    )
    monkeypatch.setattr(
        module,
        "load_all",
        lambda: {"scan_build": {"source_path": ""}, "path_rules": {"target_root": ""}},
    )
    presenter = SimpleNamespace(
        _apply_execute=lambda *args: None,
        parent=lambda: object(),
        _current_library_root_id=None,
        _on_scan_error=MagicMock(),
    )
    coord = _coord(presenter)

    coord._start_apply_worker(_plan())

    assert warnings == ["로그 경로"]


def test_start_apply_worker_starts_worker(monkeypatch) -> None:
    thread = _Thread()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(module, "UseCaseWorker", _Worker)
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(
        module,
        "load_all",
        lambda: {"scan_build": {"source_path": "/src"}, "path_rules": {"target_root": "/dest"}},
    )
    presenter = SimpleNamespace(
        _apply_execute=lambda *args: None,
        _current_library_root_id=3,
        _on_scan_error=MagicMock(),
        _progress_dialog=None,
        _on_worker_finished=MagicMock(),
        _worker_thread=None,
        parent=lambda: None,
    )
    coord = _coord(presenter)

    coord._start_apply_worker(_plan())
    thread.finished.emit()

    presenter._on_worker_finished.assert_called_once_with(thread)
    assert presenter._worker_thread is thread


def test_on_apply_worker_result_handles_error_and_rescan(monkeypatch) -> None:
    criticals: list[str] = []
    infos: list[str] = []
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "critical", lambda parent, title, body: criticals.append(title)
    )
    monkeypatch.setattr(
        module.QMessageBox, "information", lambda parent, title, body: infos.append(title)
    )
    presenter = SimpleNamespace(
        _progress_dialog=MagicMock(),
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: False,
        _scan_execute=object(),
        on_scan_clicked=MagicMock(),
        _model=MagicMock(),
        _pipeline_panel=None,
        parent=lambda: object(),
    )
    coord = _coord(presenter)

    coord._on_apply_worker_result(ApplyResult(log_path=None, moved_count=0, error="bad"), _plan())
    monkeypatch.setattr(module, "load_all", lambda: {"scan_build": {"source_path": "/scan"}})
    coord._on_apply_worker_result(ApplyResult(log_path=None, moved_count=2), _plan())

    assert criticals == ["이동 오류"]
    assert infos == ["완료"]
    presenter.on_scan_clicked.assert_called_once_with("/scan")


def test_on_apply_worker_result_merges_plan_when_no_rescan(monkeypatch) -> None:
    infos: list[str] = []
    panel = SimpleNamespace(sync_views_from_model=MagicMock())
    monkeypatch.setattr(module, "QWidget", object)
    monkeypatch.setattr(
        module.QMessageBox, "information", lambda parent, title, body: infos.append(title)
    )
    merged: list[tuple[object, object]] = []
    monkeypatch.setattr(
        module, "merge_plan_into_pipeline_rows", lambda model, plan: merged.append((model, plan))
    )
    monkeypatch.setattr(module, "load_all", lambda: {"scan_build": {"source_path": ""}})
    presenter = SimpleNamespace(
        _progress_dialog=None,
        _notify_dry_run=MagicMock(),
        _dry_run_should_enable=lambda: True,
        _scan_execute=None,
        _model=object(),
        _pipeline_panel=panel,
        parent=lambda: object(),
    )
    coord = _coord(presenter)

    plan = _plan()
    coord._on_apply_worker_result(ApplyResult(log_path=None, moved_count=1), plan)

    assert merged and merged[0][1] == plan
    panel.sync_views_from_model.assert_called_once()
    assert infos == ["완료"]
