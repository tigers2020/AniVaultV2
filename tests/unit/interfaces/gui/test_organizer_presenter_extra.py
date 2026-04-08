from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from anivault.application.dto.plan import ApplyResult, PlanResult
from anivault.interfaces.gui.models import PipelineRow
from anivault.interfaces.gui.presenters import organizer_presenter as presenter_module
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


def test_parent_widget_and_warning_helpers(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    widget = FakeWidget()
    presenter.parent = lambda: widget  # type: ignore[attr-defined]
    warnings: list[tuple[object, str, str]] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "warning",
        lambda parent, title, text: warnings.append((parent, title, text)),
    )

    assert presenter._parent_widget() is widget  # type: ignore[attr-defined]
    presenter._warn_missing_tmdb_api_key()  # type: ignore[attr-defined]

    assert warnings and warnings[0][0] is widget


def test_selected_pipeline_group_index_or_warn(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    widget = FakeWidget()
    presenter._parent_widget = lambda: widget  # type: ignore[attr-defined]
    infos: list[tuple[object, str, str]] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "information",
        lambda parent, title, text: infos.append((parent, title, text)),
    )
    panel = SimpleNamespace(selected_group_index=lambda: 1)

    assert presenter._selected_pipeline_group_index_or_warn(panel, [1, 2, 3]) == 1  # type: ignore[arg-type, attr-defined]

    panel = SimpleNamespace(selected_group_index=lambda: -1)
    assert presenter._selected_pipeline_group_index_or_warn(panel, [1, 2, 3]) is None  # type: ignore[arg-type, attr-defined]
    assert infos and infos[0][0] is widget


def test_on_plan_worker_result_handles_error_and_empty(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._progress_dialog = MagicMock()  # type: ignore[attr-defined]
    presenter._notify_dry_run = MagicMock()  # type: ignore[attr-defined]
    presenter._dry_run_should_enable = MagicMock(return_value=True)  # type: ignore[attr-defined]
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    widget = FakeWidget()
    presenter.parent = lambda: widget  # type: ignore[attr-defined]
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

    presenter._on_plan_worker_result(PlanResult(moves=(), error="bad plan"))  # type: ignore[attr-defined]
    presenter._on_plan_worker_result(PlanResult(moves=(), error=None))  # type: ignore[attr-defined]

    assert warnings == ["bad plan"]
    assert infos == ["이동할 항목이 없습니다."]
    assert presenter._progress_dialog.hide_progress.call_count == 2  # type: ignore[attr-defined]


def test_on_apply_worker_result_error_and_merge_paths(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._progress_dialog = MagicMock()  # type: ignore[attr-defined]
    presenter._notify_dry_run = MagicMock()  # type: ignore[attr-defined]
    presenter._dry_run_should_enable = MagicMock(return_value=False)  # type: ignore[attr-defined]
    presenter._scan_execute = None  # type: ignore[attr-defined]
    presenter._model = MagicMock()  # type: ignore[attr-defined]
    panel = MagicMock()
    presenter._pipeline_panel = panel  # type: ignore[attr-defined]
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    widget = FakeWidget()
    presenter.parent = lambda: widget  # type: ignore[attr-defined]
    criticals: list[str] = []
    infos: list[str] = []
    merge_calls: list[tuple[object, object]] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "critical",
        lambda parent, title, text: criticals.append(text),
    )
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "information",
        lambda parent, title, text: infos.append(text),
    )
    monkeypatch.setattr(
        presenter_module,
        "merge_plan_into_pipeline_rows",
        lambda model, plan: merge_calls.append((model, plan)),
    )
    monkeypatch.setattr(presenter_module, "load_all", lambda: {"scan_build": {"source_path": ""}})
    plan = PlanResult(moves=(), error=None)

    presenter._on_apply_worker_result(ApplyResult(moved_count=0, error="boom", log_path=None), plan)  # type: ignore[attr-defined]
    presenter._on_apply_worker_result(ApplyResult(moved_count=2, error=None, log_path=None), plan)  # type: ignore[attr-defined]

    assert criticals == ["boom"]
    assert infos == ["2개 파일을 이동했습니다."]
    assert merge_calls == [(presenter._model, plan)]  # type: ignore[attr-defined]
    panel.sync_views_from_model.assert_called_once()


def test_on_apply_worker_result_rescans_when_source_exists(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._progress_dialog = None  # type: ignore[attr-defined]
    presenter._notify_dry_run = MagicMock()  # type: ignore[attr-defined]
    presenter._dry_run_should_enable = MagicMock(return_value=True)  # type: ignore[attr-defined]
    presenter._scan_execute = object()  # type: ignore[attr-defined]
    presenter._pipeline_panel = None  # type: ignore[attr-defined]
    class FakeWidget:
        pass

    monkeypatch.setattr(presenter_module, "QWidget", FakeWidget)
    widget = FakeWidget()
    presenter.parent = lambda: widget  # type: ignore[attr-defined]
    rescans: list[str] = []
    presenter.on_scan_clicked = lambda path: rescans.append(path)  # type: ignore[attr-defined]
    infos: list[str] = []
    monkeypatch.setattr(
        presenter_module.QMessageBox,
        "information",
        lambda parent, title, text: infos.append(text),
    )
    monkeypatch.setattr(
        presenter_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Anime"}},
    )

    presenter._on_apply_worker_result(ApplyResult(moved_count=3, error=None, log_path=None), PlanResult(moves=(), error=None))  # type: ignore[attr-defined]

    assert infos == ["3개 파일을 이동했습니다."]
    assert rescans == ["F:/Anime"]
