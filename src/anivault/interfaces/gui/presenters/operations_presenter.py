"""operations_presenter.py

Operations 페이지: 플랜 생성 후 이동·폴더 트리 생성·롤백을 Worker로 실행한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from threading import Event
from typing import Any, Literal

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.application.dto.plan import ApplyInput, ApplyResult, PlanResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.use_cases.ensure_plan_directories import (
    EnsureDirsInput,
    EnsureDirsResult,
)
from anivault.application.use_cases.ensure_plan_directories import (
    execute as ensure_dirs_execute,
)
from anivault.application.use_cases.rollback_plan import execute as rollback_execute
from anivault.interfaces.gui.components.molecules import ProgressDialog
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.presenters.plan_helpers import (
    merge_plan_into_pipeline_rows,
    try_build_plan_input_from_settings,
)
from anivault.interfaces.gui.settings_storage import load_all
from anivault.interfaces.gui.state import GuiState, OperationsPhase
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

PlanExecuteFn = Callable[
    [Any, Any, Event],
    PlanResult,
]
ApplyExecuteFn = Callable[
    [Any, Any, Event],
    ApplyResult,
]


@dataclass(slots=True)
class _RollbackInput:
    """롤백 유스케이스 스텁 입력."""

    pass


class OperationsPresenter(QObject):
    """실행 탭: 플랜→적용/폴더생성/롤백을 Worker에서 처리한다."""

    execution_phase_changed = Signal(str, str)

    def __init__(
        self,
        pipeline_model: PipelineTableModel,
        plan_execute: PlanExecuteFn | None = None,
        apply_execute: ApplyExecuteFn | None = None,
        gui_state: GuiState | None = None,
        progress_dialog: ProgressDialog | None = None,
        parent: QObject | None = None,
    ) -> None:
        """파이프라인 모델과 유스케이스 실행 함수를 연결한다.

        Args:
            self: 이 Presenter.
            pipeline_model: Organizer와 공유하는 파이프라인 모델.
            plan_execute: plan_moves 클로저.
            apply_execute: apply_plan 클로저.
            gui_state: 선택적 전역 GUI 상태.
            progress_dialog: 진행 대화상자.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self._model = pipeline_model
        self._plan_execute = plan_execute
        self._apply_execute = apply_execute
        self._gui_state = gui_state
        self._progress_dialog = progress_dialog
        self._worker_thread: QThread | None = None
        self._pending_plan_for_apply: PlanResult | None = None
        self._pending_apply_mode: Literal["move", "tree"] | None = None

    def _finish_worker_session(self, dialog: ProgressDialog, hide: bool) -> None:
        """워커 finished 시 진행 세션을 닫고 필요 시 창을 숨긴다.

        Args:
            self: 이 Presenter.
            dialog: 공유 ProgressDialog.
            hide: True면 hide_progress까지 호출한다.

        Returns:
            None.
        """
        dialog.mark_work_finished()
        if hide:
            dialog.hide_progress()

    def _set_phase(self, phase: OperationsPhase, pill_text: str = "") -> None:
        """실행 탭 단계와(선택) 헤더 Pill 문구를 갱신한다.

        Args:
            self: 이 Presenter.
            phase: operations_phase 값.
            pill_text: Pill에 표시할 짧은 문구. 빈 문자열이면 phase 이름.

        Returns:
            None.
        """
        if self._gui_state is not None:
            self._gui_state.operations_phase = phase
        label = pill_text or phase.value
        self.execution_phase_changed.emit(phase.value, label)

    def _parent_widget(self) -> QWidget | None:
        """경고 대화상자용 부모 위젯을 반환한다.

        Args:
            self: 이 Presenter.

        Returns:
            QWidget 또는 None.
        """
        p = self.parent()
        return p if isinstance(p, QWidget) else None

    def on_move_files_clicked(self) -> None:
        """파일 이동: 플랜 생성 후 apply 워커를 이어서 실행한다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        self._start_plan_then("move")

    def on_create_folder_tree_clicked(self) -> None:
        """목적지 상위 폴더만 생성한다(플랜 생성 후 ensure dirs).

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        self._start_plan_then("tree")

    def _start_plan_then(self, mode: Literal["move", "tree"]) -> None:
        """검증 후 플랜 워커를 시작하고 이후 동작을 예약한다.

        Args:
            self: 이 Presenter.
            mode: move 또는 tree.

        Returns:
            None.
        """
        if self._plan_execute is None:
            return
        settings = load_all()
        rows = self._model.flat_rows()
        pr = settings.get("path_rules") or {}
        if not isinstance(pr, dict):
            pr = {}
        plan_input, err = try_build_plan_input_from_settings(rows, pr)
        parent = self._parent_widget()
        if err == "empty":
            if parent is not None:
                QMessageBox.information(
                    parent,
                    "항목 없음",
                    "먼저 Organizer에서 스캔·매칭을 완료하세요.",
                )
            self._set_phase(OperationsPhase.idle, "Ready")
            return
        if err == "path_rules" or plan_input is None:
            if parent is not None:
                QMessageBox.warning(
                    parent,
                    "경로 규칙",
                    "Settings → Path Rules에서 Target root와 Path template을 설정하세요.",
                )
            self._set_phase(OperationsPhase.idle, "Ready")
            return

        self._pending_apply_mode = mode
        self._set_phase(OperationsPhase.planning, "Planning…")
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._plan_execute,
            input_dto=plan_input,
            signals=signals,
        )
        signals.result.connect(self._on_plan_result_for_operations)
        signals.error.connect(self._on_worker_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(
                lambda: dialog.show_progress("플랜 생성", "경로 계획 중…", False)
            )
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_thread_finished(t))
        self._worker_thread = thread

    def _on_plan_result_for_operations(self, result: PlanResult) -> None:
        """플랜 결과에 따라 적용 또는 폴더 생성 워커를 시작한다.

        Args:
            self: 이 Presenter.
            result: 플랜 유스케이스 결과.

        Returns:
            None.
        """
        mode = self._pending_apply_mode
        self._pending_apply_mode = None
        parent = self._parent_widget()
        if result.error:
            if parent is not None:
                QMessageBox.warning(parent, "플랜 오류", result.error)
            self._set_phase(OperationsPhase.error, "Error")
            self._set_phase(OperationsPhase.idle, "Ready")
            return
        if not result.moves:
            if parent is not None:
                QMessageBox.information(parent, "실행", "이동할 항목이 없습니다.")
            self._set_phase(OperationsPhase.idle, "Ready")
            return

        if mode == "move":
            self._start_apply_worker(result)
        elif mode == "tree":
            self._start_ensure_dirs_worker(result)
        else:
            self._set_phase(OperationsPhase.idle, "Ready")

    def _log_root_for_apply(self) -> str | None:
        """apply·로그용 루트 경로를 설정에서 꺼낸다.

        Args:
            self: 이 Presenter.

        Returns:
            유효한 로그 루트 또는 None.
        """
        settings = load_all()
        src_root = (settings.get("scan_build") or {}).get("source_path") or ""
        path_rules = settings.get("path_rules") or {}
        target = ""
        if isinstance(path_rules, dict):
            target = str(path_rules.get("target_root") or "")
        log_root = (str(src_root).strip() or target).strip()
        return log_root or None

    def _start_apply_worker(self, plan: PlanResult) -> None:
        """파일 이동 apply 워커를 시작한다.

        Args:
            self: 이 Presenter.
            plan: 적용할 계획.

        Returns:
            None.
        """
        if self._apply_execute is None:
            self._set_phase(OperationsPhase.idle, "Ready")
            return
        log_root = self._log_root_for_apply()
        parent = self._parent_widget()
        if not log_root:
            if parent is not None:
                QMessageBox.warning(
                    parent,
                    "로그 경로",
                    "스캔 소스 경로 또는 Target root를 설정해야 합니다.",
                )
            self._set_phase(OperationsPhase.idle, "Ready")
            return

        apply_input = ApplyInput(
            operations=plan.moves,
            dry_run=False,
            log_root=log_root,
        )
        self._pending_plan_for_apply = plan
        self._set_phase(OperationsPhase.applying, "Moving…")
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=self._apply_execute,
            input_dto=apply_input,
            signals=signals,
        )
        signals.result.connect(self._on_apply_result)
        signals.error.connect(self._on_worker_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(lambda: dialog.show_progress("파일 이동", "이동 중…", False))
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_thread_finished(t))
        self._worker_thread = thread

    def _on_apply_result(self, result: ApplyResult) -> None:
        """이동 완료 후 모델·알림을 갱신한다.

        Args:
            self: 이 Presenter.
            result: 적용 결과.

        Returns:
            None.
        """
        plan = self._pending_plan_for_apply
        self._pending_plan_for_apply = None
        parent = self._parent_widget()
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        if result.error:
            if parent is not None:
                QMessageBox.critical(parent, "이동 오류", result.error)
            self._set_phase(OperationsPhase.error, "Error")
            self._set_phase(OperationsPhase.idle, "Ready")
            return
        if plan is not None:
            merge_plan_into_pipeline_rows(self._model, plan)
        if parent is not None:
            QMessageBox.information(
                parent,
                "완료",
                f"{result.moved_count}개 파일을 이동했습니다.",
            )
        self._set_phase(OperationsPhase.idle, "Ready")

    def _start_ensure_dirs_worker(self, plan: PlanResult) -> None:
        """목적지 상위 디렉터리 생성 워커를 시작한다.

        Args:
            self: 이 Presenter.
            plan: 플랜 결과.

        Returns:
            None.
        """
        inp = EnsureDirsInput(operations=plan.moves)
        self._set_phase(OperationsPhase.mkdir, "Folders…")
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=ensure_dirs_execute,
            input_dto=inp,
            signals=signals,
        )
        signals.result.connect(self._on_ensure_dirs_result)
        signals.error.connect(self._on_worker_error)
        dialog = self._progress_dialog
        if dialog is not None:
            token = dialog.mark_work_started()
            signals.started.connect(
                lambda: dialog.show_progress("폴더 생성", "목적지 폴더 생성 중…", False)
            )
            signals.progress.connect(lambda e, t=token: self._on_progress(e, t))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_thread_finished(t))
        self._worker_thread = thread

    def _on_ensure_dirs_result(self, result: EnsureDirsResult) -> None:
        """폴더 생성 결과를 알린다.

        Args:
            self: 이 Presenter.
            result: 생성 결과.

        Returns:
            None.
        """
        parent = self._parent_widget()
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        if result.error:
            if parent is not None:
                QMessageBox.critical(parent, "폴더 생성 오류", result.error)
            self._set_phase(OperationsPhase.error, "Error")
            self._set_phase(OperationsPhase.idle, "Ready")
            return
        if parent is not None:
            QMessageBox.information(
                parent,
                "완료",
                f"목적지 상위 폴더 {result.created_count}곳을 준비했습니다.",
            )
        self._set_phase(OperationsPhase.idle, "Ready")

    def on_rollback_clicked(self) -> None:
        """롤백 유스케이스를 Worker에서 실행한다.

        Args:
            self: 이 Presenter.

        Returns:
            None.
        """
        self._set_phase(OperationsPhase.rolling_back, "Undo…")
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=rollback_execute,
            input_dto=_RollbackInput(),
            signals=signals,
        )
        signals.result.connect(self._on_rollback_result)
        signals.error.connect(self._on_worker_error)
        dialog = self._progress_dialog
        if dialog is not None:
            signals.started.connect(lambda: dialog.show_progress("되돌리기", "롤백 중…", False))
            signals.finished.connect(lambda: self._finish_worker_session(dialog, True))
            dialog.canceled.connect(worker.cancel)

            def _disconnect_cancel() -> None:
                """스레드 종료 시 취소 시그널 연결을 끊는다.

                Args:
                    없음.

                Returns:
                    None.
                """
                dialog.canceled.disconnect(worker.cancel)

            thread = run_worker(worker)
            thread.finished.connect(_disconnect_cancel)
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._on_thread_finished(t))
        self._worker_thread = thread

    def _on_rollback_result(self, result: object) -> None:
        """롤백 스텁 완료 알림.

        Args:
            self: 이 Presenter.
            result: 유스케이스 반환값.

        Returns:
            None.
        """
        parent = self._parent_widget()
        if self._progress_dialog is not None:
            self._progress_dialog.hide_progress()
        if parent is not None:
            QMessageBox.information(
                parent,
                "롤백",
                "롤백 단계가 완료되었습니다. (스텁: 실제 복원은 이후 단계에서 연결)",
            )
        self._set_phase(OperationsPhase.idle, "Ready")

    def _on_progress(self, event: ProgressEvent, token: int) -> None:
        """진행률 다이얼로그를 갱신한다.

        Args:
            self: 이 Presenter.
            event: 진행 이벤트.
            token: mark_work_started에서 캡처한 세션 토큰.

        Returns:
            None.
        """
        dialog = self._progress_dialog
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            dialog.update_progress(
                message=event.message,
                value=event.percent if event.total > 0 else None,
                maximum=event.total if event.total > 0 else 100,
            )

    def _on_worker_error(self, exc: Exception) -> None:
        """워커 예외를 사용자에게 표시한다.

        Args:
            self: 이 Presenter.
            exc: 예외.

        Returns:
            None.
        """
        parent = self._parent_widget()
        if parent is not None:
            QMessageBox.critical(parent, "오류", str(exc))
        self._set_phase(OperationsPhase.error, "Error")
        self._set_phase(OperationsPhase.idle, "Ready")

    def _on_thread_finished(self, thread: QThread) -> None:
        """스레드 종료 시 참조를 정리한다.

        Args:
            self: 이 Presenter.
            thread: 종료된 스레드.

        Returns:
            None.
        """
        if self._worker_thread is thread:
            self._worker_thread = None
