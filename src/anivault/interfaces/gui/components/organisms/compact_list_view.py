"""compact_list_view.py

썸네일·제목·메타가 한 줄에 배치된 단일 열 컴팩트 리스트 뷰.

Author: Pom Kim
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label, RoundedPixmapLabel
from anivault.interfaces.gui.models import PipelineGroupRow


def _list_item_title(group: PipelineGroupRow) -> str:
    """리스트 주 라벨 문자열을 만든다(TMDB 한글 제목 우선, 없으면 파싱 제목 등).

    Args:
        group: 파이프라인 그룹 행.

    Returns:
        표시할 제목 문자열.
    """
    tmdb = (group.tmdb_korean_title_group or "").strip()
    if tmdb:
        return tmdb
    parsed = (group.parsed_title or "").strip()
    if parsed:
        return parsed
    rep = group.representative()
    base = (rep.parsed_title or "").strip()
    if base:
        return base
    if (rep.original_file or "").strip():
        return rep.original_file
    return "—"


def _list_item_meta(group: PipelineGroupRow) -> str:
    """부가 메타 줄(파일 수·연도·시즌·해상도)을 조합한다.

    Args:
        group: 파이프라인 그룹 행.

    Returns:
        ' • '로 이은 메타 문자열.
    """
    parts: list[str] = []
    if len(group.members) > 1:
        parts.append(f"{len(group.members)}개 파일")
    for p in (group.year, group.season, group.episode, group.resolution):
        s = (p or "").strip()
        if s:
            parts.append(s)
    return " • ".join(parts)


class _ListItem(QFrame):
    """한 행: 작은 포스터 썸네일과 제목·메타."""

    def __init__(self, group: PipelineGroupRow, parent: QWidget | None = None) -> None:
        """그룹 데이터로 썸네일·라벨 레이아웃을 구성한다.

        Args:
            self: 이 리스트 행 위젯.
            group: 표시할 파이프라인 그룹.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        backdrop = (group.backdrop_url or "").strip()
        poster = (group.poster_url or "").strip()
        self._image_url = backdrop or poster
        self.setStyleSheet(theme.list_item())
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(14)

        # Small thumbnail
        thumb = RoundedPixmapLabel()
        thumb.setFixedSize(48, 72)
        thumb.set_placeholder_text("—")
        layout.addWidget(thumb)
        self._thumb = thumb

        # Title + meta
        right = QVBoxLayout()
        right.setSpacing(4)
        right.setContentsMargins(0, 0, 0, 0)
        title = Label(_list_item_title(group), "title")
        title.setStyleSheet(theme.list_item_strong())
        title.setWordWrap(True)
        right.addWidget(title)
        meta_text = _list_item_meta(group)
        meta = Label(meta_text, "muted")
        meta.setStyleSheet(theme.list_item_muted())
        meta.setVisible(bool(meta_text))
        right.addWidget(meta)
        layout.addLayout(right, 1)

    @property
    def image_url(self) -> str:
        """비동기 이미지 로드에 사용할 URL(백드롭 우선, 없으면 포스터).

        Args:
            self: 이 리스트 행 위젯.

        Returns:
            이미지 URL 문자열.
        """
        return self._image_url

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """PosterCard와 동일 계약으로 썸네일 픽스맵을 갱신한다.

        Args:
            self: 이 리스트 행 위젯.
            pixmap: 표시할 픽스맵. None이면 플레이스홀더.

        Returns:
            None.
        """
        if pixmap is not None and not pixmap.isNull():
            self._thumb.set_source_pixmap(pixmap)
        else:
            self._thumb.clear_source_pixmap()
            self._thumb.set_placeholder_text("—")


class CompactListView(QFrame):
    """썸네일·제목이 있는 컴팩트 행 리스트 뷰."""

    selection_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        """스크롤 영역과 리스트 레이아웃을 초기화한다.

        Args:
            self: 이 뷰 인스턴스.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self._list_layout = QVBoxLayout(container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        scroll.setWidget(container)

        layout.addWidget(scroll)
        self.setStyleSheet(theme.card_panel())

        self._groups: list[PipelineGroupRow] = []
        self._items: list[_ListItem] = []

    def set_rows(self, groups: list[PipelineGroupRow]) -> None:
        """그룹 목록으로 리스트 행을 다시 채우고 클릭 핸들러를 연결한다.

        Args:
            self: 이 뷰 인스턴스.
            groups: 파이프라인 그룹 행 목록.

        Returns:
            None.
        """
        self._groups = list(groups)
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._items.clear()
        for i, g in enumerate(self._groups):
            w = _ListItem(g)
            w.setCursor(Qt.CursorShape.PointingHandCursor)
            w.mousePressEvent = lambda e, idx=i: self._on_click(idx)  # type: ignore[method-assign,misc]
            self._list_layout.addWidget(w)
            self._items.append(w)

    def _on_click(self, index: int) -> None:
        """행 클릭 시 선택 변경 시그널을 보낸다.

        Args:
            self: 이 뷰 인스턴스.
            index: 클릭된 행 인덱스.

        Returns:
            None.
        """
        self.selection_changed.emit(index)

    def pixmap_targets(self) -> list[_ListItem]:
        """비동기 TMDB 이미지 URL이 연결된 리스트 행(_ListItem) 목록을 반환한다.

        Args:
            self: 이 뷰 인스턴스.

        Returns:
            _ListItem 리스트 복사본.
        """
        return list(self._items)
