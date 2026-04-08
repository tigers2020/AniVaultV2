"""Dry-run, plan, and apply coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.plan import ApplyInput, ApplyResult, PlanResult
from anivault.application.dto.progress import (
    ProgressEvent,
    progress_dialog_value_and_maximum,
)
from anivault.constants.gui.components import (
    PLAN_APPLY_COMPLETE_MESSAGE_TEMPLATE,
    PLAN_APPLY_COMPLETE_TITLE,
    PLAN_APPLY_DRY_RUN_EMPTY_MESSAGE,
    PLAN_APPLY_DRY_RUN_TITLE,
    PLAN_APPLY_EMPTY_MESSAGE,
    PLAN_APPLY_EMPTY_TITLE,
    PLAN_APPLY_EXECUTE_UNAVAILABLE_MESSAGE,
    PLAN_APPLY_EXECUTE_UNAVAILABLE_TITLE,
    PLAN_APPLY_LOG_ROOT_MESSAGE,
    PLAN_APPLY_LOG_ROOT_TITLE,
    PLAN_APPLY_MOVE_ERROR_TITLE,
    PLAN_APPLY_MOVE_PROGRESS_MESSAGE,
    PLAN_APPLY_MOVE_PROGRESS_TITLE,
    PLAN_APPLY_NO_MATCHED_MESSAGE,
    PLAN_APPLY_NO_MATCHED_TITLE,
    PLAN_APPLY_PATH_RULES_MESSAGE,
    PLAN_APPLY_PATH_RULES_TITLE,
    PLAN_APPLY_PLAN_ERROR_TITLE,
    PLAN_APPLY_PLAN_PROGRESS_MESSAGE,
    PLAN_APPLY_PLAN_PROGRESS_TITLE,
)
from anivault.interfaces.gui.dialogs.dry_run_dialog import DryRunDialog
from anivault.interfaces.gui.presenters.plan_helpers import (
    merge_plan_into_pipeline_rows,
    try_build_plan_input_from_settings,
)
from anivault.interfaces.gui.presenters.worker_session import (
    run_use_case_worker_with_progress_dialog,
)
from anivault.interfaces.gui.settings_storage import load_all
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class PlanApplyCoordinator(QObject):
    """Move-plan preview and apply coordinator."""

    def __init__(self, presenter: OrganizerPresenter) -> None:
        super().__init__(presenter)
        self._p = presenter

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            value, maximum = progress_dialog_value_and_maximum(event)
            dialog.update_progress(message=event.message, value=value, maximum=maximum)

    def on_dry_run_clicked(self) -> None:
        if self._p._plan_execute is None:  # noqa: SLF001
            return
        rows = self._p._model.flat_rows()  # noqa: SLF001
        settings = load_all()
        path_rules = settings.get("path_rules") or {}
        if not isinstance(path_rules, dict):
            path_rules = {}
        plan_input, err = try_build_plan_input_from_settings(
            rows,
            path_rules,
            include_companion_subtitles=self._p._include_companion_subtitles,  # noqa: SLF001
            index_root_id=self._p._current_library_root_id,  # noqa: SLF001
        )
        parent = self._p.parent()
        if err == "empty":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_EMPTY_TITLE,
                    PLAN_APPLY_EMPTY_MESSAGE,
                )
            return
        if err == "no_matched":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_NO_MATCHED_TITLE,
                    PLAN_APPLY_NO_MATCHED_MESSAGE,
                )
            return
        if err == "path_rules" or plan_input is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    PLAN_APPLY_PATH_RULES_TITLE,
                    PLAN_APPLY_PATH_RULES_MESSAGE,
                )
            return
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._p._plan_execute,  # noqa: SLF001
            input_dto=plan_input,
            signals=signals,
        )
        signals.result.connect(self._on_plan_worker_result)
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=PLAN_APPLY_PLAN_PROGRESS_TITLE,
                message=PLAN_APPLY_PLAN_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_plan_worker_result(self, result: PlanResult) -> None:
        if self._p._progress_dialog is not None:  # noqa: SLF001
            self._p._progress_dialog.hide_progress()  # noqa: SLF001
        parent = self._p.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, PLAN_APPLY_PLAN_ERROR_TITLE, result.error)
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        if not result.moves:
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_DRY_RUN_TITLE,
                    PLAN_APPLY_DRY_RUN_EMPTY_MESSAGE,
                )
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        self._p._pending_plan = result  # noqa: SLF001
        dlg = DryRunDialog(
            [(move.source_path, move.destination_path) for move in result.moves],
            parent=parent if isinstance(parent, QWidget) else None,
        )
        dlg.apply_requested.connect(lambda: self._on_dry_run_apply_clicked(dlg))
        dlg.exec()
        self._p._pending_plan = None  # noqa: SLF001

    def _on_dry_run_apply_clicked(self, dlg: DryRunDialog) -> None:
        plan = self._p._pending_plan  # noqa: SLF001
        dlg.accept()
        parent = self._p.parent()
        if not plan:
            return
        if self._p._apply_execute is None:  # noqa: SLF001
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    PLAN_APPLY_EXECUTE_UNAVAILABLE_TITLE,
                    PLAN_APPLY_EXECUTE_UNAVAILABLE_MESSAGE,
                )
            return
        QTimer.singleShot(0, lambda p=plan: self._start_apply_worker(p))

    def _start_apply_worker(self, plan: PlanResult) -> None:
        if self._p._apply_execute is None:  # noqa: SLF001
            return
        settings = load_all()
        source_root = (settings.get("scan_build") or {}).get("source_path") or ""
        path_rules = settings.get("path_rules") or {}
        log_root = (str(source_root).strip() or path_rules.get("target_root") or "").strip()
        if not log_root:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    PLAN_APPLY_LOG_ROOT_TITLE,
                    PLAN_APPLY_LOG_ROOT_MESSAGE,
                )
            return
        apply_input = ApplyInput(
            operations=plan.moves,
            dry_run=False,
            log_root=log_root,
            source_root=str(source_root).strip() or None,
            index_root_id=self._p._current_library_root_id,  # noqa: SLF001
            organize_plan_id=plan.organize_plan_id,
            organize_item_ids=plan.organize_item_ids,
        )
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._p._apply_execute,  # noqa: SLF001
            input_dto=apply_input,
            signals=signals,
        )
        signals.result.connect(lambda r: self._on_apply_worker_result(r, plan))
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=PLAN_APPLY_MOVE_PROGRESS_TITLE,
                message=PLAN_APPLY_MOVE_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_apply_worker_result(self, result: ApplyResult, plan: PlanResult) -> None:
        if self._p._progress_dialog is not None:  # noqa: SLF001
            self._p._progress_dialog.hide_progress()  # noqa: SLF001
        parent = self._p.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.critical(parent, PLAN_APPLY_MOVE_ERROR_TITLE, result.error)
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        settings = load_all()
        scan_source = str((settings.get("scan_build") or {}).get("source_path") or "").strip()
        completion_message = PLAN_APPLY_COMPLETE_MESSAGE_TEMPLATE.format(
            moved_count=result.moved_count
        )
        if scan_source and self._p._scan_execute is not None:  # noqa: SLF001
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_COMPLETE_TITLE,
                    completion_message,
                )
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            self._p.on_scan_clicked(scan_source)
            return
        merge_plan_into_pipeline_rows(self._p._model, plan)  # noqa: SLF001
        panel = self._p._pipeline_panel  # noqa: SLF001
        if panel is not None:
            panel.sync_views_from_model()
        if isinstance(parent, QWidget):
            QMessageBox.information(
                parent,
                PLAN_APPLY_COMPLETE_TITLE,
                completion_message,
            )
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
