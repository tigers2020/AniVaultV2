"""tmdb_manual_match_dialog.py

TMDB 시리즈 수동 검색과 선택 dialog.

Author: Pom Kim
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, LineEdit
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n.keys import (
    DLG_TMDB_BTN_CANCEL,
    DLG_TMDB_BTN_OK,
    DLG_TMDB_BTN_SEARCH,
    DLG_TMDB_EMPTY_SEL_MESSAGE,
    DLG_TMDB_EMPTY_SEL_TITLE,
    DLG_TMDB_LABEL_QUERY,
    DLG_TMDB_LABEL_YEAR,
    DLG_TMDB_QUERY_PLACEHOLDER,
    DLG_TMDB_RESULT_ITEM,
    DLG_TMDB_RESULTS_TITLE,
    DLG_TMDB_TITLE,
    DLG_TMDB_UNKNOWN_TITLE,
    DLG_TMDB_UNKNOWN_YEAR,
    DLG_TMDB_YEAR_PLACEHOLDER,
)


class TmdbManualMatchDialog(QDialog):
    """검색어로 TMDB 후보를 조회하고 한 항목을 선택한다."""

    search_requested = Signal(str, object)

    def __init__(self, parent=None, *, default_query: str = "") -> None:
        super().__init__(parent)
        self.setMinimumSize(520, 420)
        self.setStyleSheet(theme.card_panel())
        self._candidates: list[TmdbSeriesCandidate] = []
        self._chosen: TmdbSeriesCandidate | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._query = LineEdit()
        dq = (default_query or "").strip()
        if dq:
            self._query.setText(dq)
        self._lbl_query = QLabel()
        form.addRow(self._lbl_query, self._query)
        self._year = LineEdit()
        self._lbl_year = QLabel()
        form.addRow(self._lbl_year, self._year)
        layout.addLayout(form)

        self._results_title = QLabel()
        layout.addWidget(self._results_title)
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list, 1)

        search_row = QHBoxLayout()
        self._search_btn = Button("", "primary")
        self._search_btn.clicked.connect(self._emit_search)
        search_row.addWidget(self._search_btn)
        search_row.addStretch(1)
        layout.addLayout(search_row)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self._ok_btn = Button("", "primary")
        self._ok_btn.clicked.connect(self._on_accept)
        self._cancel_btn = Button("", "default")
        self._cancel_btn.clicked.connect(self.reject)
        actions.addWidget(self._ok_btn)
        actions.addWidget(self._cancel_btn)
        layout.addLayout(actions)
        self.retranslate_ui()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(translate(DLG_TMDB_TITLE))
        self._lbl_query.setText(translate(DLG_TMDB_LABEL_QUERY))
        self._query.setPlaceholderText(translate(DLG_TMDB_QUERY_PLACEHOLDER))
        self._lbl_year.setText(translate(DLG_TMDB_LABEL_YEAR))
        self._year.setPlaceholderText(translate(DLG_TMDB_YEAR_PLACEHOLDER))
        self._results_title.setText(translate(DLG_TMDB_RESULTS_TITLE))
        self._search_btn.setText(translate(DLG_TMDB_BTN_SEARCH))
        self._ok_btn.setText(translate(DLG_TMDB_BTN_OK))
        self._cancel_btn.setText(translate(DLG_TMDB_BTN_CANCEL))
        self._refresh_list_labels()

    def _refresh_list_labels(self) -> None:
        if not self._candidates:
            return
        self._list.clear()
        for candidate in self._candidates:
            year = _year_label(candidate.first_air_date)
            title = (candidate.name_ko or candidate.original_name or "").strip()
            title = title or translate(DLG_TMDB_UNKNOWN_TITLE)
            sub = (candidate.original_name or "").strip()
            line = title if not sub or sub == title else f"{title} / {sub}"
            item = QListWidgetItem(
                translate(
                    DLG_TMDB_RESULT_ITEM,
                    line=line,
                    tmdb_id=candidate.tmdb_id,
                    year=year,
                )
            )
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _parse_year(self) -> int | None:
        raw = (self._year.text() or "").strip()
        if not raw:
            return None
        if raw.isdigit() and len(raw) == 4:
            return int(raw)
        return None

    def _emit_search(self) -> None:
        q = (self._query.text() or "").strip()
        self.search_requested.emit(q, self._parse_year())

    def set_search_busy(self, busy: bool) -> None:
        self._search_btn.setEnabled(not busy)
        self._query.setEnabled(not busy)
        self._year.setEnabled(not busy)

    def set_candidates(self, candidates: list[TmdbSeriesCandidate]) -> None:
        self._candidates = list(candidates)
        self._refresh_list_labels()

    def selected_candidate(self) -> TmdbSeriesCandidate | None:
        return self._chosen

    def _on_accept(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._candidates):
            QMessageBox.information(
                self,
                translate(DLG_TMDB_EMPTY_SEL_TITLE),
                translate(DLG_TMDB_EMPTY_SEL_MESSAGE),
            )
            return
        self._chosen = self._candidates[row]
        self.accept()


def _year_label(iso_date: str) -> str:
    date_text = (iso_date or "").strip()
    if len(date_text) >= 4:
        return date_text[:4]
    return translate(DLG_TMDB_UNKNOWN_YEAR)
