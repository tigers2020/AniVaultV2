"""manual_tmdb_relay.py

WorkerSignals를 수동 TMDB 대화상자로 넘기는 Qt 릴레이.

Author: Pom Kim
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog
from anivault.interfaces.gui.i18n import translate
from anivault.interfaces.gui.i18n.keys import (
    ORG_MANUAL_TMDB_ERROR_MESSAGE,
    ORG_MANUAL_TMDB_ERROR_TITLE,
)

logger = logging.getLogger(__name__)


class ManualTmdbSearchRelay(QObject):
    """WorkerSignals를 메인 스레드의 수동 매칭 대화상자로 넘긴다(큐 연결 수신자 명시)."""

    def __init__(self, dlg: TmdbManualMatchDialog, presenter: QObject) -> None:
        """대화상자와 프레젠터(부모)를 저장한다.

        Args:
            dlg: TMDB 수동 매칭 대화상자.
            presenter: OrganizerPresenter. 릴레이의 Qt 부모(스레드 소속).

        Returns:
            None.
        """
        super().__init__(presenter)
        self._dlg = dlg

    @Slot(object)
    def on_result(self, result: object) -> None:
        """검색 결과 튜플을 목록에 반영한다.

        Args:
            result: TMDB 후보 시퀀스.

        Returns:
            None.
        """
        if isinstance(result, (list, tuple)) and all(
            isinstance(candidate, TmdbSeriesCandidate) for candidate in result
        ):
            self._dlg.set_candidates(list(result))
            return
        self._dlg.set_candidates([])

    @Slot()
    def on_finished(self) -> None:
        """워커 종료 시 검색 UI를 다시 켠다.

        Returns:
            None.
        """
        self._dlg.set_search_busy(False)
        self.deleteLater()

    @Slot(Exception)
    def on_error(self, exc: Exception) -> None:
        """검색 실패 시 메시지를 띄운다.

        Args:
            exc: 예외.

        Returns:
            None.
        """
        self._dlg.set_search_busy(False)
        logger.warning("Manual TMDB search failed", exc_info=exc)
        QMessageBox.warning(
            self._dlg,
            translate(ORG_MANUAL_TMDB_ERROR_TITLE),
            translate(ORG_MANUAL_TMDB_ERROR_MESSAGE),
        )
