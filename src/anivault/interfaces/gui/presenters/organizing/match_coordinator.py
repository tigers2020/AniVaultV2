"""TMDB automatic and manual matching coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from anivault.application.ports.poster_sync_port import PosterAssetSyncPort
from anivault.application.ports.title_group_port import TitleGroupRepository
from anivault.application.ports.title_match_port import PosterAssetRepository, TitleMatchRepository
from anivault.application.use_cases.match_series import (
    apply_tmdb_candidate_to_file_rows,
    persist_manual_tmdb_selection,
)
from anivault.constants.gui.components import (
    MATCH_COORDINATOR_EMPTY_QUERY_MESSAGE,
    MATCH_COORDINATOR_EMPTY_QUERY_TITLE,
    MATCH_COORDINATOR_MISSING_API_MESSAGE,
    MATCH_COORDINATOR_MISSING_API_TITLE,
    MATCH_COORDINATOR_NO_ROWS_MESSAGE,
    MATCH_COORDINATOR_NO_ROWS_TITLE,
    MATCH_COORDINATOR_NO_SELECTION_MESSAGE,
    MATCH_COORDINATOR_NO_SELECTION_TITLE,
    MATCH_COORDINATOR_PROGRESS_MESSAGE,
    MATCH_COORDINATOR_PROGRESS_TITLE,
)
from anivault.contracts.pipeline import MatchInput, MatchResult, PipelineRow
from anivault.contracts.progress import (
    ProgressEvent,
    progress_dialog_value_and_maximum,
)
from anivault.contracts.tmdb import TmdbSearchInput, TmdbSeriesCandidate
from anivault.domain.path_norm import normalize_path_key
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog
from anivault.interfaces.gui.models import PipelineGroupRow, group_pipeline_rows
from anivault.interfaces.gui.presenters import organizer_runtime as presenter_runtime
from anivault.interfaces.gui.presenters.organizing.manual_tmdb_relay import (
    ManualTmdbSearchRelay,
)
from anivault.interfaces.gui.presenters.row_mapper import match_file_to_pipeline_row
from anivault.interfaces.gui.presenters.worker_session import (
    run_use_case_worker_with_progress_dialog,
)
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class MatchCoordinator(QObject):
    """Automatic and manual TMDB matching."""

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

    def on_match_clicked(self) -> None:
        match_execute = presenter_runtime.match_execute(self._p)
        if match_execute is None:
            parent = presenter_runtime.parent_widget(self._p)
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    MATCH_COORDINATOR_MISSING_API_TITLE,
                    MATCH_COORDINATOR_MISSING_API_MESSAGE,
                )
            return

        presenter_runtime.notify_dry_run(self._p, False)
        rows = presenter_runtime.flat_rows(self._p)
        if not rows:
            parent = presenter_runtime.parent_widget(self._p)
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    MATCH_COORDINATOR_NO_ROWS_TITLE,
                    MATCH_COORDINATOR_NO_ROWS_MESSAGE,
                )
            return

        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=match_execute,
            input_dto=MatchInput(
                files=tuple(rows),
                index_root_id=presenter_runtime.current_library_root_id(self._p),
            ),
            signals=signals,
        )
        signals.result.connect(self._on_match_result)
        signals.error.connect(lambda exc: presenter_runtime.on_scan_error(self._p, exc))
        dialog = presenter_runtime.progress_dialog(self._p)
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=MATCH_COORDINATOR_PROGRESS_TITLE,
                message=MATCH_COORDINATOR_PROGRESS_MESSAGE,
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
        thread.finished.connect(lambda t=thread: presenter_runtime.on_worker_finished(self._p, t))
        presenter_runtime.update_current_worker_thread(self._p, thread)

    def _match_file_to_pipeline_row(self, match_file: PipelineRow) -> PipelineRow:
        return match_file_to_pipeline_row(
            match_file,
            title_match=cast(
                PosterAssetRepository | None,
                presenter_runtime.title_match(self._p),
            ),
        )

    def _on_match_result(self, result: MatchResult) -> None:
        merged = [self._match_file_to_pipeline_row(row) for row in result.files]
        groups = group_pipeline_rows(merged)
        model = presenter_runtime.model(self._p)
        if not model.update_rows_if_compatible(groups):
            model.set_rows(groups)
        presenter_runtime.notify_dry_run(
            self._p,
            presenter_runtime.dry_run_should_enable(self._p),
        )

    def _warn_missing_tmdb_api_key(self) -> None:
        parent = presenter_runtime.parent_widget(self._p)
        if parent is None:
            return
        QMessageBox.warning(
            parent,
            MATCH_COORDINATOR_MISSING_API_TITLE,
            MATCH_COORDINATOR_MISSING_API_MESSAGE,
        )

    def _selected_pipeline_group_index_or_warn(
        self,
        panel: PipelineResultPanel,
        rows: list[PipelineGroupRow],
    ) -> int | None:
        idx = panel.selected_group_index()
        if 0 <= idx < len(rows):
            return idx
        parent = presenter_runtime.parent_widget(self._p)
        if parent is not None:
            QMessageBox.information(
                parent,
                MATCH_COORDINATOR_NO_SELECTION_TITLE,
                MATCH_COORDINATOR_NO_SELECTION_MESSAGE,
            )
        return None

    def _apply_manual_tmdb_candidate_to_model(
        self,
        group: PipelineGroupRow,
        chosen: TmdbSeriesCandidate,
        panel: PipelineResultPanel,
    ) -> None:
        target_paths = {member.original_file for member in group.members}
        flat_rows = presenter_runtime.flat_rows(self._p)
        files_list = list(flat_rows)
        indices = [
            index
            for index, file_row in enumerate(files_list)
            if file_row.original_file in target_paths
        ]
        if not indices:
            return

        apply_tmdb_candidate_to_file_rows(files_list, indices, chosen)
        try:
            representative_norm = normalize_path_key(files_list[indices[0]].original_file)
        except OSError:
            representative_norm = None
        persist_manual_tmdb_selection(
            files_list,
            indices,
            chosen,
            root_id=presenter_runtime.current_library_root_id(self._p),
            representative_path_norm=representative_norm,
            title_match=cast(
                TitleMatchRepository | None,
                presenter_runtime.title_match(self._p),
            ),
            title_groups=cast(
                TitleGroupRepository | None,
                presenter_runtime.title_groups(self._p),
            ),
        )
        poster_sync = cast(
            PosterAssetSyncPort | None,
            presenter_runtime.poster_sync(self._p),
        )
        if poster_sync is not None:
            poster_sync.sync_from_files(files_list)
        merged_rows = [self._match_file_to_pipeline_row(row) for row in files_list]
        merged_groups = group_pipeline_rows(merged_rows)
        pending_idx = 0
        for index, merged_group in enumerate(merged_groups):
            if any(member.original_file in target_paths for member in merged_group.members):
                pending_idx = index
                break
        panel.set_pending_selected_group_index(pending_idx)
        model = presenter_runtime.model(self._p)
        if not model.update_rows_if_compatible(merged_groups):
            model.set_rows(merged_groups)
        presenter_runtime.notify_dry_run(
            self._p,
            presenter_runtime.dry_run_should_enable(self._p),
        )

    def on_manual_tmdb_match_clicked(self) -> None:
        execute = presenter_runtime.tmdb_search_execute(self._p)
        if execute is None:
            self._warn_missing_tmdb_api_key()
            return
        panel = presenter_runtime.pipeline_panel(self._p)
        if panel is None:
            return
        rows = presenter_runtime.grouped_rows(self._p)
        idx = self._selected_pipeline_group_index_or_warn(panel, rows)
        if idx is None:
            return
        group = rows[idx]
        default_query = (group.representative().parsed_title or "").strip()
        dlg = TmdbManualMatchDialog(
            parent=presenter_runtime.parent_widget(self._p),
            default_query=default_query,
        )  # noqa: SLF001
        dlg.search_requested.connect(lambda q, y, d=dlg: self._run_tmdb_search_worker(d, q, y))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        chosen = dlg.selected_candidate()
        if chosen is None:
            return
        self._apply_manual_tmdb_candidate_to_model(group, chosen, panel)

    def _run_tmdb_search_worker(
        self,
        dlg: TmdbManualMatchDialog,
        query: str,
        year: object,
    ) -> None:
        execute = presenter_runtime.tmdb_search_execute(self._p)
        if execute is None:
            dlg.set_search_busy(False)
            return
        q = (query or "").strip()
        if not q:
            dlg.set_search_busy(False)
            parent = presenter_runtime.parent_widget(self._p)
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    MATCH_COORDINATOR_EMPTY_QUERY_TITLE,
                    MATCH_COORDINATOR_EMPTY_QUERY_MESSAGE,
                )
            return
        y: int | None = year if year is None or isinstance(year, int) else None
        signals = WorkerSignals()
        relay = ManualTmdbSearchRelay(dlg, self._p)
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=TmdbSearchInput(query=q, year=y),
            signals=signals,
        )
        presenter_runtime.set_tmdb_worker_keepalive(self._p, worker)
        signals.result.connect(relay.on_result, type=Qt.ConnectionType.QueuedConnection)
        signals.error.connect(relay.on_error, type=Qt.ConnectionType.QueuedConnection)
        signals.finished.connect(relay.on_finished, type=Qt.ConnectionType.QueuedConnection)
        dlg.set_search_busy(True)

        def _start_tmdb_thread() -> None:
            try:
                thread = run_worker(worker)
            except Exception:
                dlg.set_search_busy(False)
                return
            thread.finished.connect(
                lambda t=thread: presenter_runtime.on_worker_finished(self._p, t)
            )
            thread.finished.connect(lambda d=dlg: d.set_search_busy(False))

            def _clear_tmdb_keepalive() -> None:
                presenter_runtime.set_tmdb_worker_keepalive(self._p, None)

            thread.finished.connect(_clear_tmdb_keepalive)
            presenter_runtime.update_current_worker_thread(self._p, thread)

        QTimer.singleShot(0, _start_tmdb_thread)
