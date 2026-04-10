"""stats_grid.py

스캔·파싱·TMDB 매칭·그룹 수를 네 장의 StatCard로 보여 주는 그리드.

Author: Pom Kim
"""

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.molecules import StatCard
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K


def _fmt(n: int) -> str:
    """정수를 천 단위 구분 기호가 있는 문자열로 포맷한다.

    Args:
        n: 포맷할 정수.

    Returns:
        콤마가 들어간 문자열.
    """
    return f"{n:,}"


class StatsGrid(QWidget):
    """한 줄에 네 개의 StatCard. set_stats로 값 갱신."""

    _STAT_KEYS: tuple[str, str, str, str] = (
        K.ORG_STAT_SCANNED_FILES,
        K.ORG_STAT_PARSED_TITLES,
        K.ORG_STAT_TMDB_MATCHES,
        K.ORG_STAT_GROUPS,
    )

    def __init__(self, parent=None):
        """그리드 레이아웃·카드 위젯·고정 높이 동기화를 초기화한다.

        Args:
            self: 이 그리드 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setHorizontalSpacing(theme.inline_control_gap_px())
        layout.setVerticalSpacing(theme.inline_control_gap_px())
        layout.setContentsMargins(0, 0, 0, theme.page_section_gap_px())
        self._scanned = self._parsed = self._tmdb_matches = self._groups = 0
        self._cards = [
            StatCard(translate(self._STAT_KEYS[0]), _fmt(0)),
            StatCard(translate(self._STAT_KEYS[1]), _fmt(0)),
            StatCard(translate(self._STAT_KEYS[2]), _fmt(0)),
            StatCard(translate(self._STAT_KEYS[3]), _fmt(0)),
        ]
        for i, card in enumerate(self._cards):
            layout.addWidget(card, 0, i)

        # Prevent vertical stretching when embedded in a resizable scroll area.
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed))
        self._sync_fixed_height()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        for card, sk in zip(self._cards, self._STAT_KEYS, strict=True):
            card.set_title(translate(sk))
        self._apply_stat_values()

    def _apply_stat_values(self) -> None:
        values = (
            _fmt(self._scanned),
            _fmt(self._parsed),
            _fmt(self._tmdb_matches),
            _fmt(self._groups),
        )
        for card, v in zip(self._cards, values, strict=True):
            card.set_value(v)

    def set_stats(
        self,
        scanned: int = 0,
        parsed: int = 0,
        tmdb_matches: int = 0,
        groups: int = 0,
    ) -> None:
        """파이프라인 집계 값으로 네 장의 카드 텍스트를 갱신한다.

        Args:
            self: 이 그리드 인스턴스.
            scanned: 스캔된 파일 수.
            parsed: 파싱된 타이틀 수.
            tmdb_matches: TMDB 매칭 수.
            groups: 파이프라인 그룹(행) 수.

        Returns:
            None.
        """
        self._scanned = scanned
        self._parsed = parsed
        self._tmdb_matches = tmdb_matches
        self._groups = groups
        self._apply_stat_values()

    def _sync_fixed_height(self) -> None:
        """폰트·스타일에 맞춰 그리드 행 고정 높이를 sizeHint로 맞춘다.

        Args:
            self: 이 그리드 인스턴스.

        Returns:
            None.
        """
        layout = self.layout()
        h = int(layout.sizeHint().height()) if layout is not None else 0
        if h <= 0:
            h = int(self.sizeHint().height())
        if h > 0:
            self.setFixedHeight(h)

    def changeEvent(self, event: QEvent) -> None:
        """폰트·스타일 변경 시 행 높이를 재동기화한다.

        Args:
            self: 이 그리드 인스턴스.
            event: Qt 변경 이벤트.

        Returns:
            None.
        """
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_fixed_height()
