"""Dry-run, plan, and apply coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.constants.gui.components import (
    PIPELINE_BUSY_MESSAGE,
    PIPELINE_BUSY_TITLE,
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
from anivault.constants.gui.settings import (
    scan_source_path_from_loaded,
    target_root_from_loaded,
)
from anivault.contracts.planning import ApplyInput, ApplyResult, PlanInput, PlanResult
from anivault.contracts.progress import (
    ProgressEvent,
    progress_dialog_value_and_maximum,
)
from anivault.interfaces.gui.dialogs.dry_run_dialog import DryRunDialog
from anivault.interfaces.gui.presenters import organizer_runtime as presenter_runtime
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
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            value, maximum = progress_dialog_value_and_maximum(event)
            dialog.update_progress(message=event.message, value=value, maximum=maximum)

    @staticmethod
    def _coerce_path_rules(settings: dict[str, object]) -> dict[str, object]:
        path_rules = settings.get("path_rules") or {}
        return path_rules if isinstance(path_rules, dict) else {}

    def _dry_run_pipeline_busy_guard(self) -> bool:
        if not presenter_runtime.has_active_pipeline_work(self._p):
            return False
        parent = presenter_runtime.parent_widget(self._p)
        if isinstance(parent, QWidget):
            QMessageBox.information(parent, PIPELINE_BUSY_TITLE, PIPELINE_BUSY_MESSAGE)
        return True

    def _dry_run_plan_input_error_guard(
        self, parent: object, err: str | None, plan_input: PlanInput | None
    ) -> bool:
        if err == "empty":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_EMPTY_TITLE,
                    PLAN_APPLY_EMPTY_MESSAGE,
                )
            return True
        if err == "no_matched":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_NO_MATCHED_TITLE,
                    PLAN_APPLY_NO_MATCHED_MESSAGE,
                )
            return True
        if err == "path_rules" or plan_input is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    PLAN_APPLY_PATH_RULES_TITLE,
                    PLAN_APPLY_PATH_RULES_MESSAGE,
                )
            return True
        return False

    def _start_dry_run_plan_worker(self, execute: Any, plan_input: PlanInput) -> None:
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=plan_input,
            signals=signals,
        )
        signals.result.connect(self._on_plan_worker_result)
        signals.error.connect(lambda exc: presenter_runtime.on_scan_error(self._p, exc))
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=PLAN_APPLY_PLAN_PROGRESS_TITLE,
                message=PLAN_APPLY_PLAN_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: presenter_runtime.finish_worker_session(
                    self._p,
                    dialog,
                    hide=True,
                ),
            )
        else:
            thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)

    def on_dry_run_clicked(self) -> None:
        execute = presenter_runtime.plan_execute(self._p)
        if execute is None:
            return
        if self._dry_run_pipeline_busy_guard():
            return
        rows = presenter_runtime.flat_rows(self._p)
        settings = load_all()
        plan_input, err = try_build_plan_input_from_settings(
            rows,
            self._coerce_path_rules(settings),
            include_companion_subtitles=presenter_runtime.include_companion_subtitles(self._p),
            index_root_id=presenter_runtime.current_library_root_id(self._p),
        )
        parent = presenter_runtime.parent_widget(self._p)
        if self._dry_run_plan_input_error_guard(parent, err, plan_input):
            return
        assert plan_input is not None
        self._start_dry_run_plan_worker(execute, plan_input)

    def _on_plan_worker_result(self, result: PlanResult) -> None:
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            dialog.hide_progress()
        parent = presenter_runtime.parent_widget(self._p)
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, PLAN_APPLY_PLAN_ERROR_TITLE, result.error)
            presenter_runtime.notify_dry_run(
                self._p,
                presenter_runtime.dry_run_should_enable(self._p),
            )
            return
        if not result.moves:
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_DRY_RUN_TITLE,
                    PLAN_APPLY_DRY_RUN_EMPTY_MESSAGE,
                )
            presenter_runtime.notify_dry_run(
                self._p,
                presenter_runtime.dry_run_should_enable(self._p),
            )
            return
        presenter_runtime.set_pending_plan(self._p, result)
        dlg = DryRunDialog(
            result.moves,
            result.move_preview,
            parent=parent if isinstance(parent, QWidget) else None,
        )
        dlg.apply_requested.connect(lambda: self._on_dry_run_apply_clicked(dlg))
        dlg.exec()
        presenter_runtime.set_pending_plan(self._p, None)

    def _on_dry_run_apply_clicked(self, dlg: DryRunDialog) -> None:
        plan = presenter_runtime.pending_plan(self._p)
        dlg.accept()
        parent = presenter_runtime.parent_widget(self._p)
        if not plan:
            return
        if presenter_runtime.apply_execute(self._p) is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    PLAN_APPLY_EXECUTE_UNAVAILABLE_TITLE,
                    PLAN_APPLY_EXECUTE_UNAVAILABLE_MESSAGE,
                )
            return
        QTimer.singleShot(0, lambda p=plan: self._start_apply_worker(p))

    def _start_apply_worker(self, plan: PlanResult) -> None:
        execute = presenter_runtime.apply_execute(self._p)
        if execute is None:
            return
        if presenter_runtime.has_active_pipeline_work(self._p):
            parent = presenter_runtime.parent_widget(self._p)
            if isinstance(parent, QWidget):
                QMessageBox.information(parent, PIPELINE_BUSY_TITLE, PIPELINE_BUSY_MESSAGE)
            return
        settings = load_all()
        source_root = scan_source_path_from_loaded(settings).strip()
        log_root = source_root or target_root_from_loaded(settings).strip()
        if not log_root:
            parent = presenter_runtime.parent_widget(self._p)
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
            index_root_id=presenter_runtime.current_library_root_id(self._p),
            organize_plan_id=plan.organize_plan_id,
            organize_item_ids=plan.organize_item_ids,
        )
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=apply_input,
            signals=signals,
        )
        signals.result.connect(lambda r: self._on_apply_worker_result(r, plan))
        signals.error.connect(lambda exc: presenter_runtime.on_scan_error(self._p, exc))
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=PLAN_APPLY_MOVE_PROGRESS_TITLE,
                message=PLAN_APPLY_MOVE_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: presenter_runtime.finish_worker_session(
                    self._p,
                    dialog,
                    hide=True,
                ),
            )
        else:
            thread = run_worker(worker)
        presenter_runtime.register_worker_thread(self._p, thread)

    def _on_apply_worker_result(self, result: ApplyResult, plan: PlanResult) -> None:
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            dialog.hide_progress()
        parent = presenter_runtime.parent_widget(self._p)
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.critical(parent, PLAN_APPLY_MOVE_ERROR_TITLE, result.error)
            presenter_runtime.notify_dry_run(
                self._p,
                presenter_runtime.dry_run_should_enable(self._p),
            )
            return
        settings = load_all()
        scan_source = scan_source_path_from_loaded(settings).strip()
        completion_message = PLAN_APPLY_COMPLETE_MESSAGE_TEMPLATE.format(
            moved_count=result.moved_count
        )
        if scan_source and presenter_runtime.scan_execute(self._p) is not None:
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    PLAN_APPLY_COMPLETE_TITLE,
                    completion_message,
                )
            presenter_runtime.notify_dry_run(
                self._p,
                presenter_runtime.dry_run_should_enable(self._p),
            )
            self._p.run_scan_after_apply_completion(scan_source)
            return
        merge_plan_into_pipeline_rows(presenter_runtime.model(self._p), plan)
        panel = presenter_runtime.pipeline_panel(self._p)
        if panel is not None:
            panel.sync_views_from_model()
        if isinstance(parent, QWidget):
            QMessageBox.information(
                parent,
                PLAN_APPLY_COMPLETE_TITLE,
                completion_message,
            )
        presenter_runtime.notify_dry_run(
            self._p,
            presenter_runtime.dry_run_should_enable(self._p),
        )
