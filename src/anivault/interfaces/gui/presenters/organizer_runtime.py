"""Facade helpers for presenter/coordinator collaboration."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QWidget

from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.planning import PlanResult
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineTableModel
from anivault.interfaces.gui.presenters.row_mapper import match_file_to_pipeline_row
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker


def _call_or_attr(host: object, method_name: str, attr_name: str) -> Any:
    method = getattr(host, method_name, None)
    if callable(method):
        return method()
    return getattr(host, attr_name)


def model(host: object) -> PipelineTableModel:
    return _call_or_attr(host, "model", "_model")


def progress_dialog(host: object) -> ProgressDialog | None:
    return _call_or_attr(host, "progress_dialog", "_progress_dialog")


def parent_widget(host: object) -> QWidget | None:
    method = getattr(host, "parent_widget", None)
    if callable(method):
        return method()
    method = getattr(host, "_parent_widget", None)
    if callable(method):
        return method()
    parent = host.parent() if hasattr(host, "parent") else None
    return parent if isinstance(parent, QWidget) else None


def finish_worker_session(host: object, dialog: ProgressDialog, *, hide: bool) -> None:
    method = getattr(host, "finish_worker_session", None)
    if callable(method):
        method(dialog, hide=hide)
        return
    host._finish_worker_session(dialog, hide=hide)  # type: ignore[attr-defined]


def notify_dry_run(host: object, enabled: bool) -> None:
    method = getattr(host, "notify_dry_run", None)
    if callable(method):
        method(enabled)
        return
    host._notify_dry_run(enabled)  # type: ignore[attr-defined]


def dry_run_should_enable(host: object) -> bool:
    method = getattr(host, "dry_run_should_enable", None)
    if callable(method):
        return bool(method())
    return bool(host._dry_run_should_enable())  # type: ignore[attr-defined]


def register_worker_thread(host: object, thread: QThread) -> None:
    method = getattr(host, "register_worker_thread", None)
    if callable(method):
        method(thread)
        return
    host._worker_thread = thread  # type: ignore[attr-defined]


def on_scan_error(host: object, exc: Exception) -> None:
    method = getattr(host, "on_scan_error", None)
    if callable(method):
        method(exc)
        return
    host._on_scan_error(exc)  # type: ignore[attr-defined]


def current_library_root_id(host: object) -> int | None:
    return _call_or_attr(host, "current_library_root_id", "_current_library_root_id")


def set_current_library_root_id(host: object, value: int | None) -> None:
    method = getattr(host, "set_current_library_root_id", None)
    if callable(method):
        method(value)
        return
    host._current_library_root_id = value  # type: ignore[attr-defined]


def parse_index_root_id(host: object) -> int | None:
    return _call_or_attr(host, "parse_index_root_id", "_parse_index_root_id")


def set_parse_index_root_id(host: object, value: int | None) -> None:
    method = getattr(host, "set_parse_index_root_id", None)
    if callable(method):
        method(value)
        return
    host._parse_index_root_id = value  # type: ignore[attr-defined]


def scan_progress_handoff_done(host: object) -> bool:
    return bool(_call_or_attr(host, "scan_progress_handoff_done", "_scan_progress_handoff_done"))


def set_scan_progress_handoff_done(host: object, value: bool) -> None:
    method = getattr(host, "set_scan_progress_handoff_done", None)
    if callable(method):
        method(value)
        return
    host._scan_progress_handoff_done = value  # type: ignore[attr-defined]


def pipeline_panel(host: object) -> PipelineResultPanel | None:
    return _call_or_attr(host, "pipeline_panel", "_pipeline_panel")


def set_pipeline_panel(host: object, panel: PipelineResultPanel | None) -> None:
    method = getattr(host, "set_pipeline_result_panel", None)
    if callable(method):
        method(panel)
        return
    host._pipeline_panel = panel  # type: ignore[attr-defined]


def include_companion_subtitles(host: object) -> bool:
    return bool(_call_or_attr(host, "include_companion_subtitles", "_include_companion_subtitles"))


def exclude_subtitles_with_paired_video(host: object) -> bool:
    return bool(
        _call_or_attr(
            host,
            "exclude_subtitles_with_paired_video",
            "_exclude_subtitles_with_paired_video",
        )
    )


def pending_plan(host: object) -> PlanResult | None:
    return _call_or_attr(host, "pending_plan", "_pending_plan")


def set_pending_plan(host: object, value: PlanResult | None) -> None:
    method = getattr(host, "set_pending_plan", None)
    if callable(method):
        method(value)
        return
    host._pending_plan = value  # type: ignore[attr-defined]


def title_match(host: object) -> object | None:
    return _call_or_attr(host, "title_match_repository", "_title_match")


def title_groups(host: object) -> object | None:
    return _call_or_attr(host, "title_group_repository", "_title_groups")


def poster_sync(host: object) -> object | None:
    return _call_or_attr(host, "poster_sync_port", "_poster_sync")


def scan_execute(host: object) -> Any:
    return _call_or_attr(host, "scan_execute", "_scan_execute")


def parse_execute(host: object) -> Any:
    return _call_or_attr(host, "parse_execute", "_parse_execute")


def match_execute(host: object) -> Any:
    return _call_or_attr(host, "match_execute", "_match_execute")


def tmdb_search_execute(host: object) -> Any:
    return _call_or_attr(host, "tmdb_search_execute", "_tmdb_search_execute")


def plan_execute(host: object) -> Any:
    return _call_or_attr(host, "plan_execute", "_plan_execute")


def apply_execute(host: object) -> Any:
    return _call_or_attr(host, "apply_execute", "_apply_execute")


def sync_title_groups_execute(host: object) -> Any:
    return _call_or_attr(host, "sync_title_groups_execute", "_sync_title_groups_execute")


def cached_tmdb_hydrate_execute(host: object) -> Any:
    return _call_or_attr(host, "cached_tmdb_hydrate_execute", "_cached_tmdb_hydrate_execute")


def cached_tmdb_missing_fill_execute(host: object) -> Any:
    return _call_or_attr(
        host,
        "cached_tmdb_missing_fill_execute",
        "_cached_tmdb_missing_fill_execute",
    )


def set_tmdb_worker_keepalive(host: object, worker: UseCaseWorker | None) -> None:
    method = getattr(host, "set_tmdb_worker_keepalive", None)
    if callable(method):
        method(worker)
        return
    host._tmdb_worker_keepalive = worker  # type: ignore[attr-defined]


def map_match_file_to_pipeline_row(host: object, match_file: PipelineRow) -> PipelineRow:
    method = getattr(host, "match_file_to_pipeline_row", None)
    if callable(method):
        return method(match_file)
    method = getattr(host, "_match_file_to_pipeline_row", None)
    if callable(method):
        return method(match_file)
    return match_file_to_pipeline_row(match_file)


def set_rows(host: object, rows: list[PipelineRow]) -> None:
    method = getattr(host, "set_rows", None)
    if callable(method):
        method(rows)
        return
    model(host).set_rows(rows)  # type: ignore[arg-type]


def grouped_rows(host: object) -> list[PipelineGroupRow]:
    rows_method = getattr(model(host), "rows", None)
    if callable(rows_method):
        return rows_method()
    return []


def flat_rows(host: object) -> list[PipelineRow]:
    return model(host).flat_rows()


def on_worker_finished(host: object, thread: QThread) -> None:
    method = getattr(host, "on_worker_finished", None)
    if callable(method):
        method(thread)
        return
    host._on_worker_finished(thread)  # type: ignore[attr-defined]


def update_current_worker_thread(host: object, thread: QThread) -> None:
    method = getattr(host, "set_current_worker_thread", None)
    if callable(method):
        method(thread)
        return
    host._worker_thread = thread  # type: ignore[attr-defined]
