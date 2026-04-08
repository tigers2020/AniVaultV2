"""TMDB automatic and manual matching coordinator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.progress import (
    ProgressEvent,
    progress_dialog_value_and_maximum,
)
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
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
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow, group_pipeline_rows
from anivault.interfaces.gui.presenters.organizing.manual_tmdb_relay import (
    ManualTmdbSearchRelay,
)
from anivault.interfaces.gui.presenters.plan_helpers import pipeline_row_to_match_file
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
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None and not dialog.is_progress_token_valid(token):
            return
        if dialog is not None:
            value, maximum = progress_dialog_value_and_maximum(event)
            dialog.update_progress(message=event.message, value=value, maximum=maximum)

    def on_match_clicked(self) -> None:
        match_execute = self._p._match_execute  # noqa: SLF001
        if match_execute is None:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    MATCH_COORDINATOR_MISSING_API_TITLE,
                    MATCH_COORDINATOR_MISSING_API_MESSAGE,
                )
            return

        self._p._notify_dry_run(False)  # noqa: SLF001
        rows = self._p._model.flat_rows()  # noqa: SLF001
        if not rows:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    MATCH_COORDINATOR_NO_ROWS_TITLE,
                    MATCH_COORDINATOR_NO_ROWS_MESSAGE,
                )
            return

        files = tuple(pipeline_row_to_match_file(row) for row in rows)
        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=match_execute,
            input_dto=MatchInput(
                files=files,
                index_root_id=self._p._current_library_root_id,  # noqa: SLF001
            ),
            signals=signals,
        )
        signals.result.connect(self._on_match_result)
        signals.error.connect(self._p._on_scan_error)  # noqa: SLF001
        dialog = self._p._progress_dialog  # noqa: SLF001
        if dialog is not None:
            thread = run_use_case_worker_with_progress_dialog(
                dialog=dialog,
                worker=worker,
                signals=signals,
                title=MATCH_COORDINATOR_PROGRESS_TITLE,
                message=MATCH_COORDINATOR_PROGRESS_MESSAGE,
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _match_file_to_pipeline_row(self, match_file: MatchFileRow) -> PipelineRow:
        local_poster: str | None = None
        title_match = self._p._title_match  # noqa: SLF001
        if title_match is not None:
            tmdb_series_id = (match_file.tmdb_series_id or "").strip()
            remote_poster_path = normalize_tmdb_remote_image_path(match_file.tmdb_poster_path)
            if tmdb_series_id and remote_poster_path:
                try:
                    local_poster = title_match.get_poster_local_path(
                        int(tmdb_series_id), "poster", remote_poster_path
                    )
                except (OSError, TypeError, ValueError):
                    local_poster = None
        poster_display = resolve_final_poster_display_source(local_poster, match_file.poster_url)
        return PipelineRow(
            original_file=match_file.original_file,
            parsed_title=match_file.parsed_title,
            parse_group=match_file.parse_group,
            tmdb_korean_title_group=match_file.tmdb_korean_title_group,
            tmdb_series_id=match_file.tmdb_series_id,
            tmdb_poster_path=match_file.tmdb_poster_path,
            tmdb_backdrop_path=match_file.tmdb_backdrop_path,
            year=match_file.year,
            season=match_file.season,
            resolution=match_file.resolution,
            status=match_file.status,
            poster_url=poster_display,
            backdrop_url=match_file.backdrop_url,
            target_path=match_file.target_path,
            episode=match_file.episode,
        )

    def _on_match_result(self, result: MatchResult) -> None:
        merged = [self._match_file_to_pipeline_row(row) for row in result.files]
        groups = group_pipeline_rows(merged)
        model = self._p._model  # noqa: SLF001
        if not model.update_rows_if_compatible(groups):
            model.set_rows(groups)
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001

    def _warn_missing_tmdb_api_key(self) -> None:
        parent = self._p._parent_widget()  # noqa: SLF001
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
        parent = self._p._parent_widget()  # noqa: SLF001
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
        chosen: TmdbSeriesCandidateDTO,
        panel: PipelineResultPanel,
    ) -> None:
        target_paths = {member.original_file for member in group.members}
        flat_rows = self._p._model.flat_rows()  # noqa: SLF001
        files_list = [pipeline_row_to_match_file(row) for row in flat_rows]
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
            root_id=self._p._current_library_root_id,  # noqa: SLF001
            representative_path_norm=representative_norm,
            title_match=self._p._title_match,  # noqa: SLF001
            title_groups=self._p._title_groups,  # noqa: SLF001
        )
        poster_sync = self._p._poster_sync  # noqa: SLF001
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
        model = self._p._model  # noqa: SLF001
        if not model.update_rows_if_compatible(merged_groups):
            model.set_rows(merged_groups)
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001

    def on_manual_tmdb_match_clicked(self) -> None:
        execute = self._p._tmdb_search_execute  # noqa: SLF001
        if execute is None:
            self._warn_missing_tmdb_api_key()
            return
        panel = self._p._pipeline_panel  # noqa: SLF001
        if panel is None:
            return
        rows = self._p._model.rows()  # noqa: SLF001
        idx = self._selected_pipeline_group_index_or_warn(panel, rows)
        if idx is None:
            return
        group = rows[idx]
        default_query = (group.representative().parsed_title or "").strip()
        dlg = TmdbManualMatchDialog(
            parent=self._p._parent_widget(),
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
        execute = self._p._tmdb_search_execute  # noqa: SLF001
        if execute is None:
            dlg.set_search_busy(False)
            return
        q = (query or "").strip()
        if not q:
            dlg.set_search_busy(False)
            parent = self._p.parent()
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
        self._p._tmdb_worker_keepalive = worker  # noqa: SLF001
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
            thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
            thread.finished.connect(lambda d=dlg: d.set_search_busy(False))

            def _clear_tmdb_keepalive() -> None:
                self._p._tmdb_worker_keepalive = None  # noqa: SLF001

            thread.finished.connect(_clear_tmdb_keepalive)
            self._p._worker_thread = thread  # noqa: SLF001

        QTimer.singleShot(0, _start_tmdb_thread)
