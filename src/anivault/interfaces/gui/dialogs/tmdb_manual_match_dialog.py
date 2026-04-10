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

from anivault.constants.gui.components import (
    TMDB_MANUAL_DIALOG_BUTTON_CANCEL,
    TMDB_MANUAL_DIALOG_BUTTON_OK,
    TMDB_MANUAL_DIALOG_BUTTON_SEARCH,
    TMDB_MANUAL_DIALOG_EMPTY_SELECTION_MESSAGE,
    TMDB_MANUAL_DIALOG_EMPTY_SELECTION_TITLE,
    TMDB_MANUAL_DIALOG_LABEL_QUERY,
    TMDB_MANUAL_DIALOG_LABEL_YEAR,
    TMDB_MANUAL_DIALOG_QUERY_PLACEHOLDER,
    TMDB_MANUAL_DIALOG_RESULT_ITEM_TEMPLATE,
    TMDB_MANUAL_DIALOG_RESULTS_TITLE,
    TMDB_MANUAL_DIALOG_TITLE,
    TMDB_MANUAL_DIALOG_UNKNOWN_TITLE,
    TMDB_MANUAL_DIALOG_UNKNOWN_YEAR,
    TMDB_MANUAL_DIALOG_YEAR_PLACEHOLDER,
)
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, LineEdit


class TmdbManualMatchDialog(QDialog):
    """검색어로 TMDB 후보를 조회하고 한 항목을 선택한다."""

    search_requested = Signal(str, object)

    def __init__(self, parent=None, *, default_query: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(TMDB_MANUAL_DIALOG_TITLE)
        self.setMinimumSize(520, 420)
        self.setStyleSheet(theme.card_panel())
        self._candidates: list[TmdbSeriesCandidate] = []
        self._chosen: TmdbSeriesCandidate | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._query = LineEdit()
        self._query.setPlaceholderText(TMDB_MANUAL_DIALOG_QUERY_PLACEHOLDER)
        dq = (default_query or "").strip()
        if dq:
            self._query.setText(dq)
        form.addRow(TMDB_MANUAL_DIALOG_LABEL_QUERY, self._query)
        self._year = LineEdit()
        self._year.setPlaceholderText(TMDB_MANUAL_DIALOG_YEAR_PLACEHOLDER)
        form.addRow(TMDB_MANUAL_DIALOG_LABEL_YEAR, self._year)
        layout.addLayout(form)

        layout.addWidget(QLabel(TMDB_MANUAL_DIALOG_RESULTS_TITLE))
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list, 1)

        search_row = QHBoxLayout()
        self._search_btn = Button(TMDB_MANUAL_DIALOG_BUTTON_SEARCH, "primary")
        self._search_btn.clicked.connect(self._emit_search)
        search_row.addWidget(self._search_btn)
        search_row.addStretch(1)
        layout.addLayout(search_row)

        actions = QHBoxLayout()
        actions.addStretch(1)
        ok_btn = Button(TMDB_MANUAL_DIALOG_BUTTON_OK, "primary")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn = Button(TMDB_MANUAL_DIALOG_BUTTON_CANCEL, "default")
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(ok_btn)
        actions.addWidget(cancel_btn)
        layout.addLayout(actions)

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
        self._list.clear()
        for candidate in self._candidates:
            year = _year_label(candidate.first_air_date)
            title = (candidate.name_ko or candidate.original_name or "").strip()
            title = title or TMDB_MANUAL_DIALOG_UNKNOWN_TITLE
            sub = (candidate.original_name or "").strip()
            line = title if not sub or sub == title else f"{title} / {sub}"
            item = QListWidgetItem(
                TMDB_MANUAL_DIALOG_RESULT_ITEM_TEMPLATE.format(
                    line=line,
                    tmdb_id=candidate.tmdb_id,
                    year=year,
                )
            )
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def selected_candidate(self) -> TmdbSeriesCandidate | None:
        return self._chosen

    def _on_accept(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._candidates):
            QMessageBox.information(
                self,
                TMDB_MANUAL_DIALOG_EMPTY_SELECTION_TITLE,
                TMDB_MANUAL_DIALOG_EMPTY_SELECTION_MESSAGE,
            )
            return
        self._chosen = self._candidates[row]
        self.accept()


def _year_label(iso_date: str) -> str:
    date_text = (iso_date or "").strip()
    if len(date_text) >= 4:
        return date_text[:4]
    return TMDB_MANUAL_DIALOG_UNKNOWN_YEAR
