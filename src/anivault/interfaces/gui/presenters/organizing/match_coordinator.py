"""match_coordinator.py

TMDB 매칭·수동 검색 흐름.

Author: Pom Kim
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.progress import ProgressEvent, progress_dialog_value_and_maximum
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.use_cases.match_series import (
    apply_tmdb_candidate_to_file_rows,
    persist_manual_tmdb_selection,
)
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.poster_display import resolve_final_poster_display_source
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineRow,
    group_pipeline_rows,
)
from anivault.interfaces.gui.presenters.organizing.manual_tmdb_relay import ManualTmdbSearchRelay
from anivault.interfaces.gui.presenters.plan_helpers import (
    pipeline_row_to_match_file,
)
from anivault.interfaces.gui.presenters.worker_session import (
    run_use_case_worker_with_progress_dialog,
)
from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class MatchCoordinator(QObject):
    """자동·수동 TMDB 매칭."""

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

    def on_match_clicked(self) -> None:
        """현재 평탄화된 파이프라인 행으로 TMDB 매칭 워커를 실행한다.

        Returns:
            None.
        """
        match_execute = self._p._match_execute  # noqa: SLF001
        if match_execute is None:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(
                    parent,
                    "TMDB API 키 없음",
                    "Settings → Parse/TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요.",
                )
            return
        self._p._notify_dry_run(False)  # noqa: SLF001
        rows = self._p._model.flat_rows()  # noqa: SLF001
        if not rows:
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.information(
                    parent,
                    "매칭할 항목 없음",
                    "먼저 폴더를 스캔하고 파싱이 끝난 뒤 다시 시도하세요.",
                )
            return
        files = tuple(pipeline_row_to_match_file(r) for r in rows)
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
                title="TMDB 매칭",
                message="한글 제목 조회 중…",
                indeterminate=False,
                on_progress_with_token=self._on_progress,
                on_finished=lambda: self._p._finish_worker_session(dialog, True),  # noqa: SLF001
            )
        else:
            thread = run_worker(worker)
        thread.finished.connect(lambda t=thread: self._p._on_worker_finished(t))  # noqa: SLF001
        self._p._worker_thread = thread  # noqa: SLF001

    def _match_file_to_pipeline_row(self, m: MatchFileRow) -> PipelineRow:
        """MatchFileRow를 PipelineRow로 변환한다.

        Args:
            m: 매칭 결과 파일 행.

        Returns:
            파이프라인 테이블 행.
        """
        local_poster: str | None = None
        tm = self._p._title_match  # noqa: SLF001
        if tm is not None:
            tid_s = (m.tmdb_series_id or "").strip()
            rp = normalize_tmdb_remote_image_path(m.tmdb_poster_path)
            if tid_s and rp:
                try:
                    local_poster = tm.get_poster_local_path(int(tid_s), "poster", rp)
                except (OSError, TypeError, ValueError):
                    local_poster = None
        poster_display = resolve_final_poster_display_source(local_poster, m.poster_url)
        return PipelineRow(
            original_file=m.original_file,
            parsed_title=m.parsed_title,
            parse_group=m.parse_group,
            tmdb_korean_title_group=m.tmdb_korean_title_group,
            tmdb_series_id=m.tmdb_series_id,
            tmdb_poster_path=m.tmdb_poster_path,
            tmdb_backdrop_path=m.tmdb_backdrop_path,
            year=m.year,
            season=m.season,
            resolution=m.resolution,
            status=m.status,
            poster_url=poster_display,
            backdrop_url=m.backdrop_url,
            target_path=m.target_path,
            episode=m.episode,
        )

    def _on_match_result(self, result: MatchResult) -> None:
        """매칭 결과를 PipelineRow로 변환해 그룹화 후 모델에 반영한다.

        Args:
            result: TMDB 매칭 유스케이스 결과.

        Returns:
            None.
        """
        merged = [self._match_file_to_pipeline_row(m) for m in result.files]
        self._p._model.set_rows(group_pipeline_rows(merged))  # noqa: SLF001
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001

    def _warn_missing_tmdb_api_key(self) -> None:
        """TMDB 검색 실행 함수가 없을 때 사용자에게 안내한다.

        Returns:
            None.
        """
        parent = self._p._parent_widget()  # noqa: SLF001
        if parent is None:
            return
        QMessageBox.warning(
            parent,
            "TMDB API 키 없음",
            "Settings → Parse/TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요.",
        )

    def _selected_pipeline_group_index_or_warn(
        self,
        panel: PipelineResultPanel,
        rows: list[PipelineGroupRow],
    ) -> int | None:
        """파이프라인에서 항목이 선택되었는지 확인하고 그룹 인덱스를 반환한다.

        Args:
            panel: 파이프라인 결과 패널.
            rows: 그룹 행 목록.

        Returns:
            유효한 선택이면 인덱스, 아니면 None.
        """
        idx = panel.selected_group_index()
        if 0 <= idx < len(rows):
            return idx
        parent = self._p._parent_widget()  # noqa: SLF001
        if parent is not None:
            QMessageBox.information(
                parent,
                "선택 없음",
                "파이프라인에서 항목을 먼저 선택하세요.",
            )
        return None

    def _apply_manual_tmdb_candidate_to_model(
        self,
        group: PipelineGroupRow,
        chosen: TmdbSeriesCandidateDTO,
        panel: PipelineResultPanel,
    ) -> None:
        """수동 선택한 TMDB 후보를 그룹에 반영하고 모델을 갱신한다.

        Args:
            group: 적용 대상 파이프라인 그룹.
            chosen: 선택된 TMDB 시리즈 후보.
            panel: 파이프라인 결과 패널.

        Returns:
            None.
        """
        target_paths = {m.original_file for m in group.members}
        flat = self._p._model.flat_rows()  # noqa: SLF001
        files_list = [pipeline_row_to_match_file(r) for r in flat]
        indices = [i for i, f in enumerate(files_list) if f.original_file in target_paths]
        if not indices:
            return
        apply_tmdb_candidate_to_file_rows(files_list, indices, chosen)
        try:
            rep_norm = normalize_path_key(files_list[indices[0]].original_file)
        except OSError:
            rep_norm = None
        persist_manual_tmdb_selection(
            files_list,
            indices,
            chosen,
            root_id=self._p._current_library_root_id,  # noqa: SLF001
            representative_path_norm=rep_norm,
            title_match=self._p._title_match,  # noqa: SLF001
            title_groups=self._p._title_groups,  # noqa: SLF001
        )
        poster_sync = self._p._poster_sync  # noqa: SLF001
        if poster_sync is not None:
            poster_sync.sync_from_files(files_list)
        merged_rows = [self._match_file_to_pipeline_row(m) for m in files_list]
        merged_groups = group_pipeline_rows(merged_rows)
        pending_idx = 0
        for i, g in enumerate(merged_groups):
            if any(m.original_file in target_paths for m in g.members):
                pending_idx = i
                break
        panel.set_pending_selected_group_index(pending_idx)
        self._p._model.set_rows(merged_groups)  # noqa: SLF001
        self._p._notify_dry_run(self._p._dry_run_should_enable())  # noqa: SLF001

    def on_manual_tmdb_match_clicked(self) -> None:
        """세부 정보 패널에서 TMDB 수동 매칭을 요청한다.

        Returns:
            None.
        """
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
            parent=self._p._parent_widget(), default_query=default_query
        )  # noqa: SLF001
        dlg.search_requested.connect(
            lambda q, y, d=dlg: self._run_tmdb_search_worker(d, q, y),
        )
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
        """다이얼로그 검색 요청에 대해 TMDB 검색 워커를 시작한다.

        Args:
            dlg: 수동 매칭 대화상자.
            query: 검색어.
            year: 연도 또는 None.

        Returns:
            None.
        """
        execute = self._p._tmdb_search_execute  # noqa: SLF001
        if execute is None:
            dlg.set_search_busy(False)
            return
        q = (query or "").strip()
        if not q:
            dlg.set_search_busy(False)
            parent = self._p.parent()
            if isinstance(parent, QWidget):
                QMessageBox.warning(parent, "검색어 없음", "검색어를 입력하세요.")
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
            """검색 시그널 처리 후 QThread를 시작한다."""
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
