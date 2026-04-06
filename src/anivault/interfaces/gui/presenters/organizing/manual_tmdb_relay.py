"""manual_tmdb_relay.py

WorkerSignals를 수동 TMDB 대화상자로 넘기는 Qt 릴레이.

Author: Pom Kim
"""

from collections.abc import Sequence
from typing import cast

from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QMessageBox

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.interfaces.gui.dialogs.tmdb_manual_match_dialog import TmdbManualMatchDialog


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
        self._dlg.set_candidates(list(cast(Sequence[TmdbSeriesCandidateDTO], result)))

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
        QMessageBox.warning(self._dlg, "TMDB 검색 실패", str(exc))
