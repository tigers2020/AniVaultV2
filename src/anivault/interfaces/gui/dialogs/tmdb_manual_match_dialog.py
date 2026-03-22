"""tmdb_manual_match_dialog.py

TMDB 시리즈 수동 검색·결과 선택 대화상자.

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

from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Button, LineEdit


class TmdbManualMatchDialog(QDialog):
    """검색어로 TMDB 후보를 조회하고 한 항목을 선택한다."""

    search_requested = Signal(str, object)

    def __init__(self, parent=None, *, default_query: str = "") -> None:
        """입력 필드·목록·버튼을 구성한다.

        Args:
            self: 이 대화상자.
            parent: 부모 위젯.
            default_query: 검색어 칸에 미리 넣을 문자열(예: 선택 행의 parsed_title).

        Returns:
            None.
        """
        super().__init__(parent)
        self.setWindowTitle("TMDB 수동 매칭")
        self.setMinimumSize(520, 420)
        self.setStyleSheet(theme.card_panel())
        self._candidates: list[TmdbSeriesCandidateDTO] = []
        self._chosen: TmdbSeriesCandidateDTO | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._query = LineEdit()
        self._query.setPlaceholderText("검색어 (예: 원하는 작품 제목)")
        dq = (default_query or "").strip()
        if dq:
            self._query.setText(dq)
        form.addRow("검색어", self._query)
        self._year = LineEdit()
        self._year.setPlaceholderText("비우면 연도 무시 (예: 2024)")
        form.addRow("연도(선택)", self._year)
        layout.addLayout(form)

        layout.addWidget(QLabel("검색 결과"))
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list, 1)

        search_row = QHBoxLayout()
        self._search_btn = Button("검색", "primary")
        self._search_btn.clicked.connect(self._emit_search)
        search_row.addWidget(self._search_btn)
        search_row.addStretch(1)
        layout.addLayout(search_row)

        actions = QHBoxLayout()
        actions.addStretch(1)
        ok_btn = Button("확인", "primary")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn = Button("취소", "default")
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(ok_btn)
        actions.addWidget(cancel_btn)
        layout.addLayout(actions)

    def _parse_year(self) -> int | None:
        """연도 입력란을 정수 또는 None으로 해석한다.

        Args:
            self: 이 대화상자.

        Returns:
            방영 연도. 비어 있으면 None.
        """
        raw = (self._year.text() or "").strip()
        if not raw:
            return None
        if raw.isdigit() and len(raw) == 4:
            return int(raw)
        return None

    def _emit_search(self) -> None:
        """검색 요청 시그널을 보낸다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        q = (self._query.text() or "").strip()
        self.search_requested.emit(q, self._parse_year())

    def set_search_busy(self, busy: bool) -> None:
        """검색 중 버튼·입력 비활성화.

        Args:
            self: 이 대화상자.
            busy: True면 검색 중.

        Returns:
            None.
        """
        self._search_btn.setEnabled(not busy)
        self._query.setEnabled(not busy)
        self._year.setEnabled(not busy)

    def set_candidates(self, candidates: list[TmdbSeriesCandidateDTO]) -> None:
        """검색 결과 목록을 채운다.

        Args:
            self: 이 대화상자.
            candidates: TMDB 후보 목록.

        Returns:
            None.
        """
        self._candidates = list(candidates)
        self._list.clear()
        for c in self._candidates:
            y = _year_label(c.first_air_date)
            title = (c.name_ko or c.original_name or "").strip() or "—"
            sub = (c.original_name or "").strip()
            line = f"{title}"
            if sub and sub != title:
                line = f"{title} / {sub}"
            item = QListWidgetItem(f"{line}\nID {c.tmdb_id} · {y}")
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def selected_candidate(self) -> TmdbSeriesCandidateDTO | None:
        """확인으로 확정된 후보를 반환한다.

        Args:
            self: 이 대화상자.

        Returns:
            선택된 후보. 없으면 None.
        """
        return self._chosen

    def _on_accept(self) -> None:
        """목록에서 선택한 후보로 확정한다.

        Args:
            self: 이 대화상자.

        Returns:
            None.
        """
        row = self._list.currentRow()
        if row < 0 or row >= len(self._candidates):
            QMessageBox.information(
                self,
                "선택 없음",
                "목록에서 항목을 선택하거나 검색 결과가 있어야 합니다.",
            )
            return
        self._chosen = self._candidates[row]
        self.accept()


def _year_label(iso_date: str) -> str:
    """first_air_date에서 연도 표시 문자열을 만든다.

    Args:
        iso_date: YYYY-MM-DD 등.

    Returns:
        연도 또는 placeholder.
    """
    d = (iso_date or "").strip()
    if len(d) >= 4:
        return d[:4]
    return "—"
