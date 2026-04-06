"""content_view.py

왼쪽은 스크롤 가능한 컴팩트 카드 목록, 오른쪽은 메타데이터 패널인 콘텐츠 뷰.

Author: Pom Kim
"""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PosterCard
from anivault.interfaces.gui.models import PipelineGroupRow, pipeline_group_display_image_url


class ContentView(QFrame):
    """좌측 리스트·우측 상세 텍스트로 구성된 콘텐츠 레이아웃."""

    selection_changed = Signal(int)

    def __init__(self, parent=None):
        """스플리터·스크롤·메타 라벨과 내부 상태를 초기화한다.

        Args:
            self: 이 뷰 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: compact list
        left = QFrame()
        left.setMinimumWidth(260)
        left.setMaximumWidth(420)
        left.setStyleSheet(theme.card_panel())
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet(theme.scroll_area_transparent())
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(4)
        left_scroll.setWidget(self._list_container)
        left_layout.addWidget(left_scroll)
        splitter.addWidget(left)

        # Right: scrollable info only
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(theme.scroll_area_transparent())
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._meta_scroll_content = QWidget()
        meta_content_layout = QVBoxLayout(self._meta_scroll_content)
        meta_content_layout.setContentsMargins(8, 8, 8, 8)

        self._meta_frame = QFrame()
        self._meta_frame.setObjectName("content_view_text_panel")
        self._meta_frame.setStyleSheet(theme.content_view_text_panel_overlay())
        meta_layout = QVBoxLayout(self._meta_frame)
        meta_layout.setContentsMargins(8, 8, 8, 8)
        self._meta_label = Label("", "muted")
        self._meta_label.setWordWrap(True)
        self._meta_label.setStyleSheet(theme.panel_header_desc())
        meta_layout.addWidget(self._meta_label)
        meta_content_layout.addWidget(self._meta_frame)
        meta_content_layout.addStretch(1)

        right_scroll.setWidget(self._meta_scroll_content)
        right_layout.addWidget(right_scroll)
        splitter.addWidget(right)

        splitter.setSizes([320, 900])
        layout.addWidget(splitter)
        self.setStyleSheet(theme.card_panel())

        self._groups: list[PipelineGroupRow] = []
        self._cards: list[PosterCard] = []
        self._selected_index = -1

    def poster_cards(self) -> list[PosterCard]:
        """좌측 목록에 배치된 PosterCard 목록의 복사본을 반환한다.

        Args:
            self: 이 뷰 인스턴스.

        Returns:
            PosterCard 리스트.
        """
        return list(self._cards)

    def _clear_list_widgets(self) -> None:
        """좌측 리스트 레이아웃의 자식 위젯을 모두 제거한다.

        Args:
            self: 이 뷰 인스턴스.

        Returns:
            None.
        """
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()

    @staticmethod
    def _compact_meta_for_group(g: PipelineGroupRow) -> str:
        """카드 하단에 쓸 컴팩트 메타 문자열을 만든다.

        Args:
            g: 파이프라인 그룹 행.

        Returns:
            ' • '로 이은 메타 문자열.
        """
        meta_parts: list[str] = []
        if len(g.members) > 1:
            meta_parts.append(f"{len(g.members)}개 파일")
        for p in (g.year, g.season, g.resolution):
            s = (p or "").strip()
            if s:
                meta_parts.append(s)
        return " • ".join(meta_parts)

    @staticmethod
    def _group_card_title(g: PipelineGroupRow) -> str:
        """그룹 카드 제목(TMDB 한글 그룹 제목 우선, 없으면 파싱 제목).

        Args:
            g: 파이프라인 그룹 행.

        Returns:
            카드 제목 문자열.
        """
        return (g.tmdb_korean_title_group or "").strip() or (g.parsed_title or "").strip()

    def _add_group_card(self, index: int, g: PipelineGroupRow) -> None:
        """지정 인덱스에 맞는 클릭 가능한 컴팩트 PosterCard를 좌측 목록에 추가한다.

        Args:
            self: 이 뷰 인스턴스.
            index: 선택 시 전달할 행 인덱스.
            g: 표시할 파이프라인 그룹.

        Returns:
            None.
        """
        card = PosterCard(
            title=self._group_card_title(g),
            meta=self._compact_meta_for_group(g),
            path="",
            image_url=pipeline_group_display_image_url(g),
            variant="compact",
            image_aspect="backdrop",
            text_panel_overlay=True,
        )
        card.setMinimumWidth(220)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.mousePressEvent = lambda e, idx=index: self._on_select(idx)  # type: ignore[method-assign,misc]
        self._list_layout.addWidget(card)
        self._cards.append(card)

    def set_rows(self, groups: list[PipelineGroupRow]) -> None:
        """그룹 목록으로 좌측 카드 목록을 재구성하고 첫 항목을 선택한다.

        Args:
            self: 이 뷰 인스턴스.
            groups: 파이프라인 그룹 행 목록.

        Returns:
            None.
        """
        self._groups = list(groups)
        self._clear_list_widgets()
        self._cards.clear()
        for i, g in enumerate(self._groups):
            self._add_group_card(i, g)
        self._selected_index = -1
        if self._groups:
            self._on_select(0)

    @staticmethod
    def _meta_html_for_group(g: PipelineGroupRow) -> str:
        """우측 메타 패널에 표시할 HTML 문자열을 생성한다.

        Args:
            g: 파이프라인 그룹 행.

        Returns:
            QLabel용 HTML 본문.
        """
        if len(g.members) > 1:
            files_html = "<br>".join(Path(m.original_file).name for m in g.members)
            return (
                f"<b>파일 ({len(g.members)}개)</b><br>{files_html}<br><br>"
                f"<b>Parsed:</b> {g.parsed_title}<br>"
                f"<b>TMDB:</b> {g.tmdb_korean_title_group}<br>"
                f"<b>연도/시즌:</b> {g.year} / {g.season}<br>"
                f"<b>해상도:</b> {g.resolution}<br>"
                f"<b>경로:</b> {g.target_path}"
            )
        r = g.members[0]
        return (
            f"<b>원본 파일:</b> {r.original_file}<br>"
            f"<b>Parsed:</b> {r.parsed_title}<br>"
            f"<b>TMDB:</b> {r.tmdb_korean_title_group}<br>"
            f"<b>연도/시즌:</b> {r.year} / {r.season}<br>"
            f"<b>해상도:</b> {r.resolution}<br>"
            f"<b>경로:</b> {r.target_path}"
        )

    def _on_select(self, index: int) -> None:
        """선택 인덱스에 맞는 메타 HTML을 표시하고 selection_changed를 emit한다.

        Args:
            self: 이 뷰 인스턴스.
            index: 선택된 그룹 인덱스.

        Returns:
            None.
        """
        self._selected_index = index
        g = self._groups[index]
        self._meta_label.setText(self._meta_html_for_group(g))
        self.selection_changed.emit(index)
