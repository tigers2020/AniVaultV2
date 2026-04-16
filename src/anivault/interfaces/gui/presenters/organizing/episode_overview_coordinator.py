"""Coordinator for the episode overview dialog flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QWidget

from anivault.contracts.tmdb import TmdbSeasonOverviewInput, TvSeasonOverview
from anivault.interfaces.gui.dialogs import EpisodeOverviewDialog
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n import translate
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    build_episode_slot_view_models,
    extract_first_season_number,
)
from anivault.interfaces.gui.presenters import organizer_runtime as presenter_runtime
from anivault.interfaces.gui.workers import UseCaseWorker, WorkerSignals, run_worker

if TYPE_CHECKING:
    from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


class EpisodeOverviewCoordinator:
    """Open and populate the episode overview dialog."""

    def __init__(self, presenter: OrganizerPresenter) -> None:
        self._p = presenter
        self._dialog: EpisodeOverviewDialog | None = None

    def open_group_index(self, index: int) -> None:
        execute = presenter_runtime.tv_season_overview_execute(self._p)
        if execute is None:
            self._warn(
                translate(K.ORG_MATCH_MISSING_API_TITLE),
                translate(K.ORG_MATCH_MISSING_API_MESSAGE),
            )
            return
        rows = presenter_runtime.grouped_rows(self._p)
        if not (0 <= index < len(rows)):
            return
        group = rows[index]
        tv_id = self._tv_id_for_group(group)
        if tv_id is None:
            self._warn(
                translate(K.ORG_EP_OVERVIEW_MATCH_REQUIRED_TITLE),
                translate(K.ORG_EP_OVERVIEW_MATCH_REQUIRED_MESSAGE),
            )
            return
        season_number = extract_first_season_number(group.representative().season)
        dialog = self._ensure_dialog()
        dialog.set_context(
            (group.tmdb_korean_title_group or group.parsed_title or "").strip(),
            season_number,
        )
        dialog.show_loading()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

        signals = WorkerSignals()
        worker = UseCaseWorker(
            execute_fn=execute,
            input_dto=TmdbSeasonOverviewInput(tv_id=tv_id, season_number=season_number),
            signals=signals,
        )
        signals.result.connect(
            lambda overview, g=group, d=dialog: self._on_result(d, g, overview),
            type=Qt.ConnectionType.QueuedConnection,
        )
        signals.error.connect(
            lambda exc, d=dialog: self._on_error(d, exc),
            type=Qt.ConnectionType.QueuedConnection,
        )
        presenter_runtime.register_worker_thread(self._p, run_worker(worker))

    def _ensure_dialog(self) -> EpisodeOverviewDialog:
        if self._dialog is None:
            self._dialog = EpisodeOverviewDialog(parent=presenter_runtime.parent_widget(self._p))
        return self._dialog

    @staticmethod
    def _tv_id_for_group(group: PipelineGroupRow) -> int | None:
        raw = (group.representative().tmdb_series_id or "").strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except ValueError:
            return None
        return value if value > 0 else None

    def _on_result(
        self,
        dialog: EpisodeOverviewDialog,
        group: PipelineGroupRow,
        overview: TvSeasonOverview | None,
    ) -> None:
        if overview is None or not overview.episodes:
            dialog.show_empty()
            self._warn(
                translate(K.ORG_EP_OVERVIEW_LOAD_FAILED_TITLE),
                translate(K.ORG_EP_OVERVIEW_LOAD_FAILED_MESSAGE, error=""),
            )
            return
        dialog.set_context(
            (group.tmdb_korean_title_group or group.parsed_title or "").strip(),
            overview.season_number,
        )
        dialog.show_slots(build_episode_slot_view_models(group, overview))

    def _on_error(self, dialog: EpisodeOverviewDialog, exc: Exception) -> None:
        dialog.show_empty()
        self._warn(
            translate(K.ORG_EP_OVERVIEW_LOAD_FAILED_TITLE),
            translate(K.ORG_EP_OVERVIEW_LOAD_FAILED_MESSAGE, error=str(exc)),
        )

    def _warn(self, title: str, message: str) -> None:
        parent = presenter_runtime.parent_widget(self._p)
        QMessageBox.warning(parent if isinstance(parent, QWidget) else None, title, message)
