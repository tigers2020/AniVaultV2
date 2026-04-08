"""plan_apply_coordinator.py

Dry-run·플랜·적용 워커 흐름.

Author: Pom Kim
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.plan import ApplyInput, ApplyResult, PlanResult
from anivault.application.dto.progress import ProgressEvent, progress_dialog_value_and_maximum
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
    """이동 계획 미리보기와 실제 적용."""

    def __init__(self, presenter: OrganizerPresenter) -> None:
        """호스트 프레젠터를 부모로 둔다.

        Args:
            presenter: OrganizerPresenter 인스턴스.

        Returns:
            None.
        """
        super().__init__(presenter)
        self._p = presenter

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        """ProgressEvent로 진행 다이얼로그를 갱신한다.

        Args:
            event: 진행률 이벤트 DTO.
            token: 세션 토큰.

        Returns:
            None.
        """
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            value, maximum = progress_dialog_value_and_maximum(event)
            dialog.update_progress(
                message=event.message,
                value=value,
                maximum=maximum,
            )

    def on_dry_run_clicked(self) -> None:
        """Dry Run: 이동 계획 워커를 실행한 뒤 미리보기 대화상자를 연다.

        Returns:
            None.
        """
        if self._p._plan_execute is None:  # noqa: SLF001
            return
        rows = self._p._model.flat_rows()  # noqa: SLF001
        settings = load_all()
        pr = settings.get("path_rules") or {}
        if not isinstance(pr, dict):
            pr = {}
        plan_input, err = try_build_plan_input_from_settings(
            rows,
            pr,
            include_companion_subtitles=self._p._include_companion_subtitles,  # noqa: SLF001
            index_root_id=self._p._current_library_root_id,  # noqa: SLF001
        )
        parent = self._p.parent()
        if err == "empty":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "항목 없음",
                    "먼저 스캔·매칭을 완료하세요.",
                )
            return
        if err == "no_matched":
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "TMDB 매칭 없음",
                    "TMDB 한글 제목이 있는 항목이 없습니다. 자동·수동 매칭으로 준비한 뒤 다시 시도하세요.",
                )
            return
        if err == "path_rules" or plan_input is None:
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "경로 규칙",
                    "Settings → Path Rules에서 Target root와 Path template을 설정하세요.",
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
                title="플랜 생성",
                message="경로 계획 중…",
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_plan_worker_result(self, result: PlanResult) -> None:
        """플랜 결과로 Dry Run 대화상자를 띄운다.

        Args:
            result: 계획 유스케이스 결과.

        Returns:
            None.
        """
        if self._p._progress_dialog is not None:  # noqa: SLF001
            self._p._progress_dialog.hide_progress()  # noqa: SLF001
        parent = self._p.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, "플랜 오류", result.error)
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        if not result.moves:
            if isinstance(parent, QWidget):
                QMessageBox.information(parent, "Dry Run", "이동할 항목이 없습니다.")
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        self._p._pending_plan = result  # noqa: SLF001
        dlg = DryRunDialog(
            [(m.source_path, m.destination_path) for m in result.moves],
            parent=parent if isinstance(parent, QWidget) else None,
        )
        dlg.apply_requested.connect(lambda: self._on_dry_run_apply_clicked(dlg))
        dlg.exec()
        self._p._pending_plan = None  # noqa: SLF001

    def _on_dry_run_apply_clicked(self, dlg: DryRunDialog) -> None:
        """미리보기에서 실제 이동을 요청한다.

        Args:
            dlg: Dry Run 대화상자.

        Returns:
            None.
        """
        plan = self._p._pending_plan  # noqa: SLF001
        dlg.accept()
        parent = self._p.parent()
        if not plan:
            return
        if self._p._apply_execute is None:  # noqa: SLF001
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "실제 이동 불가",
                    "실제 이동 기능이 연결되지 않았습니다. 앱을 다시 실행해 주세요.",
                )
            return
        QTimer.singleShot(0, lambda p=plan: self._start_apply_worker(p))

    def _start_apply_worker(self, plan: PlanResult) -> None:
        """apply 유스케이스 워커를 시작한다.

        Args:
            plan: 실행할 계획.

        Returns:
            None.
        """
        if self._p._apply_execute is None:  # noqa: SLF001
            return
        settings = load_all()
        src_root = (settings.get("scan_build") or {}).get("source_path") or ""
        path_rules = settings.get("path_rules") or {}
        log_root = (str(src_root).strip() or path_rules.get("target_root") or "").strip()
        if not log_root:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "로그 경로",
                    "스캔 소스 경로 또는 Target root를 설정해야 합니다.",
                )
            return
        apply_input = ApplyInput(
            operations=plan.moves,
            dry_run=False,
            log_root=log_root,
            source_root=str(src_root).strip() or None,
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
                title="파일 이동",
                message="이동 중…",
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _on_apply_worker_result(self, result: ApplyResult, plan: PlanResult) -> None:
        """적용 워커 완료 시 모델·알림을 갱신한다.

        Args:
            result: 적용 유스케이스 결과.
            plan: 이번에 적용한 계획.

        Returns:
            None.
        """
        if self._p._progress_dialog is not None:  # noqa: SLF001
            self._p._progress_dialog.hide_progress()  # noqa: SLF001
        parent = self._p.parent()
        if result.error:
            if isinstance(parent, QWidget):
                QMessageBox.critical(parent, "이동 오류", result.error)
            self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
            return
        settings = load_all()
        scan_source = str((settings.get("scan_build") or {}).get("source_path") or "").strip()
        if scan_source and self._p._scan_execute is not None:  # noqa: SLF001
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "완료",
                    f"{result.moved_count}개 파일을 이동했습니다.",
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
                "완료",
                f"{result.moved_count}개 파일을 이동했습니다.",
            )
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001
