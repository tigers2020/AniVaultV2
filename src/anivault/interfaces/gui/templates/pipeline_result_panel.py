"""pipeline_result_panel.py

파이프라인 결과 영역: 보기 전환·테이블·콘텐츠·포스터 그리드·상세 패널을 통합한다.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Protocol, TypedDict

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from anivault.constants.gui.components import (
    PIPELINE_RESULT_PANEL_HEADER_DESCRIPTION,
    PIPELINE_RESULT_PANEL_HEADER_TITLE,
    PIPELINE_RESULT_PANEL_MATCHED_LABEL,
    PIPELINE_RESULT_PANEL_UNMATCHED_LABEL,
)
from anivault.constants.gui.navigation import ICON_SIZES, LEGACY_VIEW_KEY_MAP, VIEW_TO_INDEX
from anivault.interfaces.gui.components.molecules import (
    PanelHeader,
    PosterCard,
    ViewToggleBar,
)
from anivault.interfaces.gui.components.molecules.poster_card import (
    COMPACT_TITLE_ONLY_BODY_HEIGHT_PX,
)
from anivault.interfaces.gui.components.molecules.view_toggle_bar import (
    VIEW_CONTENT,
    VIEW_DETAILS,
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_ICON_XL,
)
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import DetailsPane
from anivault.interfaces.gui.components.organisms.pipeline_table import PipelineTable
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_row_ready_for_plan,
)
from anivault.interfaces.gui.services.image_loader import ImageLoader
from anivault.interfaces.gui.settings_storage import load_all, save_all


class _ImageRowTarget(Protocol):
    """비동기 이미지 URL과 픽스맵 적용 계약(PosterCard 등)."""

    @property
    def image_url(self) -> str:
        """비동기 로드에 사용할 이미지 URL.

        Args:
            self: 이미지 행 대상.

        Returns:
            이미지 URL 문자열.
        """
        ...

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """로드된 픽스맵을 위젯에 반영한다.

        Args:
            self: 이미지 행 대상.
            pixmap: 표시할 픽스맵. None이면 비움.

        Returns:
            None.
        """
        ...


class PipelineResultUiState(TypedDict):
    """Persisted UI state payload for PipelineResultPanel."""

    view_key: str
    selected_index: int


DEFAULT_UI_STATE: PipelineResultUiState = {
    "view_key": VIEW_DETAILS,
    "selected_index": -1,
}


class PipelineResultPanel(QFrame):
    """보기 전환과 선택 가능한 우측 패널을 갖춘 통합 파이프라인 결과 위젯."""

    selection_changed = Signal(int)
    manual_match_requested = Signal()

    def __init__(
        self,
        model: PipelineTableModel | None = None,
        parent=None,
    ):
        """하위 뷰·스플리터·시그널을 구성하고 저장된 UI 상태를 복원한다.

        Args:
            self: 이 패널 인스턴스.
            model: 공유 파이프라인 테이블 모델. None이면 내부에서 생성.
            parent: Qt 부모 위젯.

        Returns:
            None.
        """
        super().__init__(parent)
        self._model = model if model is not None else PipelineTableModel()
        self._rows: list[PipelineGroupRow] = []
        self._selected_index = -1
        self._restoring_state = False
        self._pending_selected_index = -1
        self._cards_by_url: dict[str, list[_ImageRowTarget]] = {}
        self._image_loader = ImageLoader(self)
        self._image_loader.loaded.connect(self._on_poster_image_loaded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view_bar = ViewToggleBar()
        self._header = PanelHeader(
            PIPELINE_RESULT_PANEL_HEADER_TITLE,
            PIPELINE_RESULT_PANEL_HEADER_DESCRIPTION,
            right_widget=self._view_bar,
        )
        layout.addWidget(self._header)
        # Keep the header ("label") height stable; let the table/content consume remaining space.
        self._header.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        )
        self._sync_header_height()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Main content: stacked views
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self._stack.setMinimumHeight(0)

        # 0: Details — 한글 제목 있음 / 없음 세로 분할(행 status와 별개; 상단 라벨은 집계 구역 제목)
        self._matched_model = PipelineTableModel()
        self._unmatched_model = PipelineTableModel()
        self._matched_table = PipelineTable(show_header=False, model=self._matched_model)
        self._unmatched_table = PipelineTable(show_header=False, model=self._unmatched_model)
        self._matched_table.selection_changed.connect(
            lambda r: self._on_split_table_selection("matched", r)
        )
        self._unmatched_table.selection_changed.connect(
            lambda r: self._on_split_table_selection("unmatched", r)
        )
        details_splitter = QSplitter(Qt.Orientation.Vertical)
        details_splitter.setChildrenCollapsible(False)
        top_wrap = QWidget()
        top_l = QVBoxLayout(top_wrap)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.setSpacing(4)
        _lbl_m = QLabel(PIPELINE_RESULT_PANEL_MATCHED_LABEL)
        top_l.addWidget(_lbl_m)
        top_l.addWidget(self._matched_table, 1)
        bottom_wrap = QWidget()
        bottom_l = QVBoxLayout(bottom_wrap)
        bottom_l.setContentsMargins(0, 0, 0, 0)
        bottom_l.setSpacing(4)
        _lbl_u = QLabel(PIPELINE_RESULT_PANEL_UNMATCHED_LABEL)
        bottom_l.addWidget(_lbl_u)
        bottom_l.addWidget(self._unmatched_table, 1)
        details_splitter.addWidget(top_wrap)
        details_splitter.addWidget(bottom_wrap)
        details_splitter.setStretchFactor(0, 1)
        details_splitter.setStretchFactor(1, 1)
        self._stack.addWidget(details_splitter)

        # 1: Content
        content_view = ContentView()
        content_view.selection_changed.connect(self._on_selection)
        self._stack.addWidget(content_view)
        self._content_view = content_view

        # 2-5: Icon grids (XL, L, M, S)
        self._poster_grids: dict[str, PosterGrid] = {}
        for key in (VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S):
            grid = PosterGrid(
                min_card_width=ICON_SIZES[key],
                show_header=False,
                body_below_image_px=COMPACT_TITLE_ONLY_BODY_HEIGHT_PX,
            )
            self._stack.addWidget(grid)
            self._poster_grids[key] = grid
        self._poster_grid_dirty: dict[str, bool] = dict.fromkeys(self._poster_grids, True)

        main_splitter.addWidget(self._stack)

        # Right pane: empty placeholder or DetailsPane
        self._pane_stack = QStackedWidget()
        self._pane_stack.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        )
        self._pane_stack.setMinimumHeight(0)
        self._pane_stack.addWidget(QWidget())  # empty
        self._details_pane = DetailsPane()
        self._pane_stack.addWidget(self._details_pane)
        main_splitter.addWidget(self._pane_stack)
        self._details_pane.manual_match_requested.connect(self.manual_match_requested.emit)
        self._main_splitter = main_splitter
        self._main_splitter.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        self._main_splitter.setMinimumHeight(0)
        self._pane_width = 340
        self._main_min_width = 320
        main_splitter.setSizes([960, 0])
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 0)

        layout.addWidget(main_splitter)
        # Vertical stretch: header(0) is fixed, splitter(1) fills remaining space.
        layout.setStretchFactor(self._header, 0)
        layout.setStretchFactor(main_splitter, 1)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))
        self.setMinimumHeight(0)

        self._view_bar.view_changed.connect(self._on_view_changed)

        # Sync content/poster grids when model changes
        self._model.modelReset.connect(self._sync_views_from_model)
        self._restore_ui_state()

    def _apply_list_content_for_view_key(self, key: str, rows: list[PipelineGroupRow]) -> None:
        """보기 키에 맞게만 콘텐츠 뷰를 채운다.

        테이블·아이콘 보기일 때 비가시 콘텐츠 뷰에 수천 행 위젯을 만들지 않아 modelReset 시 메인 스레드 점유를 줄인다.

        Args:
            self: 이 패널 인스턴스.
            key: 현재 또는 전환할 보기 키.
            rows: 모델 그룹 행.

        Returns:
            None.
        """
        if key == VIEW_CONTENT:
            self._content_view.set_rows(rows)
        else:
            self._content_view.set_rows([])

    def _on_view_changed(self, key: str) -> None:
        """보기 키에 맞게 스택 인덱스·포스터 그리드·이미지를 동기화하고 상태를 저장한다.

        Args:
            self: 이 패널 인스턴스.
            key: ViewToggleBar 보기 키.

        Returns:
            None.
        """
        if key in VIEW_TO_INDEX:
            self._stack.setCurrentIndex(VIEW_TO_INDEX[key])
        self._view_bar.set_current_view(key)
        rows = list(self._model.rows())
        self._apply_list_content_for_view_key(key, rows)
        grid_cards = self._ensure_poster_grid_for_view_key(key, rows)
        self._set_details_pane_visible(key in {VIEW_ICON_XL, VIEW_ICON_L, VIEW_ICON_M, VIEW_ICON_S})
        combined = list(self._content_view.poster_cards())
        combined.extend(grid_cards)
        self._refresh_all_poster_pixmaps(combined)
        self._persist_ui_state()

    def _unified_index_for_group(self, group: PipelineGroupRow) -> int:
        """파생 테이블의 그룹이 통합 `_rows`에서 몇 번째인지 찾는다.

        Args:
            self: 이 패널 인스턴스.
            group: 파이프라인 그룹 행.

        Returns:
            통합 인덱스. 없으면 -1.
        """
        if not group.members:
            return -1
        key = group.members[0].original_file
        for i, g in enumerate(self._rows):
            if any(m.original_file == key for m in g.members):
                return i
        return -1

    def _on_split_table_selection(self, which: str, row: int) -> None:
        """세부 테이블에서 선택 시 통합 그룹 인덱스로 변환해 반영한다.

        Args:
            self: 이 패널 인스턴스.
            which: "matched" 또는 "unmatched".
            row: 해당 파생 테이블의 행 인덱스.

        Returns:
            None.
        """
        model = self._matched_model if which == "matched" else self._unmatched_model
        groups = model.rows()
        if row < 0 or row >= len(groups):
            return
        uni = self._unified_index_for_group(groups[row])
        if uni >= 0:
            self._apply_unified_selection(uni)

    def _sync_split_tables_selection(self, unified_index: int) -> None:
        """통합 인덱스에 맞춰 상·하단 테이블 중 하나만 하이라이트한다.

        Args:
            self: 이 패널 인스턴스.
            unified_index: 통합 그룹 인덱스. 범위 밖이면 선택 해제.

        Returns:
            None.
        """
        if unified_index < 0 or unified_index >= len(self._rows):
            self._matched_table.select_row(-1)
            self._unmatched_table.select_row(-1)
            return
        key = self._rows[unified_index].members[0].original_file
        for i, g in enumerate(self._matched_model.rows()):
            if any(m.original_file == key for m in g.members):
                self._matched_table.select_row(i)
                self._unmatched_table.select_row(-1)
                return
        for i, g in enumerate(self._unmatched_model.rows()):
            if any(m.original_file == key for m in g.members):
                self._unmatched_table.select_row(i)
                self._matched_table.select_row(-1)
                return
        self._matched_table.select_row(-1)
        self._unmatched_table.select_row(-1)

    def _apply_unified_selection(self, index: int) -> None:
        """통합 그룹 인덱스로 상세 패널·분할 테이블 선택을 맞춘다.

        Args:
            self: 이 패널 인스턴스.
            index: 통합 그룹 인덱스.

        Returns:
            None.
        """
        self._selected_index = index
        self.selection_changed.emit(index)
        row = self._rows[index] if 0 <= index < len(self._rows) else None
        self._details_pane.set_row(row)
        self._sync_split_tables_selection(index)
        self._persist_ui_state()

    def _on_selection(self, index: int) -> None:
        """선택 인덱스를 반영하고 상세 패널과 외부 시그널을 갱신한다.

        Args:
            self: 이 패널 인스턴스.
            index: 그룹 행 인덱스. 범위 밖이면 빈 선택.

        Returns:
            None.
        """
        self._apply_unified_selection(index)

    def _set_details_pane_visible(self, visible: bool) -> None:
        """우측 세부 정보 패널의 표시 상태를 직접 설정한다.

        Args:
            self: 이 패널 인스턴스.
            visible: 상세 패널 표시 여부.

        Returns:
            None.
        """
        if visible:
            self._pane_stack.setCurrentIndex(1)
            w = self._main_splitter.width()
            self._main_splitter.setSizes(
                [max(self._main_min_width, w - self._pane_width), self._pane_width]
            )
        else:
            self._pane_stack.setCurrentIndex(0)
            w = self._main_splitter.width()
            self._main_splitter.setSizes([w, 0])

    def _on_icon_grid_card_clicked(self, index: int) -> None:
        """아이콘 카드 클릭 시 상세 패널을 유지한 채 해당 행을 선택한다.

        Args:
            self: 이 패널 인스턴스.
            index: 그룹 행 인덱스.

        Returns:
            None.
        """
        self._set_details_pane_visible(True)
        self._on_selection(index)

    def _make_card_clickable(self, card: PosterCard, index: int) -> None:
        """포스터 카드 클릭 시 해당 행을 선택하도록 커서·마우스 핸들러를 연결한다.

        Args:
            self: 이 패널 인스턴스.
            card: 클릭 가능하게 할 포스터 카드.
            index: 선택할 그룹 행 인덱스.

        Returns:
            None.
        """
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        def _on_press(_event: object) -> None:
            self._on_icon_grid_card_clicked(index)

        card.mousePressEvent = _on_press  # type: ignore[assignment]

    def _clear_all_poster_grids(self) -> None:
        """아이콘 그리드 위젯을 비우고 모두 재구성 필요로 표시한다.

        Args:
            self: 이 패널.

        Returns:
            None.
        """
        for key, grid in self._poster_grids.items():
            grid.set_cards([])
            self._poster_grid_dirty[key] = True

    def _make_compact_grid_cards(self, rows: list[PipelineGroupRow]) -> list[PosterCard]:
        """파이프라인 그룹 행으로 아이콘 그리드용 포스터+제목만 PosterCard 목록을 만든다.

        Args:
            self: 이 패널.
            rows: 그룹 행 목록.

        Returns:
            PosterCard 인스턴스 리스트.
        """
        cards: list[PosterCard] = []
        for g in rows:
            title = (g.tmdb_korean_title_group or "").strip() or (g.parsed_title or "").strip()
            cards.append(
                PosterCard(
                    title=title,
                    meta="",
                    path="",
                    image_url=g.poster_url,
                    variant="compact",
                    title_only=True,
                )
            )
        return cards

    def _ensure_poster_grid_for_view_key(
        self, view_key: str, rows: list[PipelineGroupRow]
    ) -> list[PosterCard]:
        """현재 보기 키가 아이콘 그리드면 카드를 필요 시 한 번만 구성한다.

        Args:
            self: 이 패널.
            view_key: ViewToggleBar 보기 키.
            rows: 모델 그룹 행.

        Returns:
            해당 그리드의 PosterCard 목록. 아이콘 보기가 아니면 빈 목록.
        """
        grid = self._poster_grids.get(view_key)
        if grid is None:
            return []
        if not self._poster_grid_dirty.get(view_key, True):
            return grid.cards()
        cards = self._make_compact_grid_cards(rows)
        for i, card in enumerate(cards):
            self._make_card_clickable(card, i)
        grid.set_cards(cards)
        self._poster_grid_dirty[view_key] = False
        return cards

    def _on_poster_image_loaded(self, url: str, pixmap: QPixmap) -> None:
        """ImageLoader 완료 시 해당 URL을 참조하는 모든 대상에 픽스맵을 적용한다.

        Args:
            self: 이 패널 인스턴스.
            url: 로드된 이미지 URL.
            pixmap: 디코딩된 픽스맵.

        Returns:
            None.
        """
        for card in self._cards_by_url.get(url, []):
            card.set_pixmap(pixmap if not pixmap.isNull() else None)

    def _refresh_all_poster_pixmaps(self, cards: list[PosterCard]) -> None:
        """카드의 HTTP URL을 수집해 캐시 또는 비동기 로드로 픽스맵을 갱신한다.

        Args:
            self: 이 패널 인스턴스.
            cards: 갱신할 포스터 카드 목록.

        Returns:
            None.
        """
        self._cards_by_url.clear()
        for card in cards:
            u = (card.image_url or "").strip()
            if u:
                self._cards_by_url.setdefault(u, []).append(card)
        for url in self._cards_by_url:
            cached = self._image_loader.get(url)
            if cached is not None:
                for c in self._cards_by_url[url]:
                    c.set_pixmap(cached)
            else:
                self._image_loader.load(url)

    def _sync_views_from_model(self) -> None:
        """modelReset 시 콘텐츠·그리드 뷰를 모델과 동기화한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        rows = self._model.rows()
        self._rows = list(rows)

        flat = self._model.flat_rows()
        matched_flat = [r for r in flat if pipeline_row_ready_for_plan(r)]
        unmatched_flat = [r for r in flat if not pipeline_row_ready_for_plan(r)]
        self._matched_model.set_rows(group_pipeline_rows(matched_flat))
        self._unmatched_model.set_rows(group_pipeline_rows(unmatched_flat))

        self._clear_all_poster_grids()
        self._apply_list_content_for_view_key(self._view_bar.current_view(), rows)
        all_poster_cards: list[PosterCard] = []
        all_poster_cards.extend(self._content_view.poster_cards())
        vk = self._view_bar.current_view()
        all_poster_cards.extend(self._ensure_poster_grid_for_view_key(vk, self._rows))
        self._refresh_all_poster_pixmaps(all_poster_cards)
        if rows:
            index = self._selectable_index(len(rows))
            self._on_selection(index)
        else:
            self._on_selection(-1)

    def _selectable_index(self, length: int) -> int:
        """대기·현재 선택 상태에 맞는 유효한 행 인덱스를 반환한다.

        Args:
            self: 이 패널 인스턴스.
            length: 그룹 행 개수.

        Returns:
            선택 인덱스. 없으면 -1.
        """
        if length <= 0:
            return -1
        if 0 <= self._pending_selected_index < length:
            idx = self._pending_selected_index
            self._pending_selected_index = -1
            return idx
        if 0 <= self._selected_index < length:
            return self._selected_index
        return 0

    def _restore_ui_state(self) -> None:
        """설정 저장소에서 Pipeline Result UI 상태를 읽어 위젯에 적용한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        ui_state = load_all().get("ui_state", {})
        pipeline_state = {}
        if isinstance(ui_state, dict):
            raw = ui_state.get("pipeline_results", {})
            if isinstance(raw, dict):
                pipeline_state = raw
        normalized = self._normalize_ui_state(pipeline_state)
        self._restoring_state = True
        self._pending_selected_index = normalized["selected_index"]
        self._on_view_changed(normalized["view_key"])
        self._restoring_state = False

    def _normalize_ui_state(self, data: dict[str, object]) -> PipelineResultUiState:
        """저장된 ui_state 딕셔너리를 안전한 기본값이 채워진 형태로 정규화한다.

        Args:
            self: 이 패널 인스턴스.
            data: 원시 설정 딕셔너리.

        Returns:
            정규화된 UI 상태.
        """
        view_key = data.get("view_key")
        selected_index = data.get("selected_index")
        normalized: PipelineResultUiState = {
            "view_key": DEFAULT_UI_STATE["view_key"],
            "selected_index": DEFAULT_UI_STATE["selected_index"],
        }
        if isinstance(view_key, str):
            view_key = LEGACY_VIEW_KEY_MAP.get(view_key, view_key)
            if view_key in VIEW_TO_INDEX:
                normalized["view_key"] = view_key
        if isinstance(selected_index, int):
            normalized["selected_index"] = selected_index
        return normalized

    def _persist_ui_state(self) -> None:
        """현재 Pipeline Result UI 상태를 설정 저장소에 기록한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        if self._restoring_state:
            return
        save_all(
            {
                "ui_state": {
                    "pipeline_results": {
                        "view_key": self._view_bar.current_view(),
                        "selected_index": self._selected_index,
                    }
                }
            }
        )

    def model(self) -> PipelineTableModel:
        """프레젠터가 갱신할 공유 파이프라인 테이블 모델을 반환한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            PipelineTableModel 인스턴스.
        """
        return self._model

    def selected_group_index(self) -> int:
        """현재 선택된 파이프라인 그룹 인덱스를 반환한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            행 인덱스. 없으면 -1.
        """
        return self._selected_index

    def set_pending_selected_group_index(self, index: int) -> None:
        """modelReset 직후 `_sync_views_from_model`에서 쓸 선택 인덱스를 예약한다.

        Args:
            self: 이 패널 인스턴스.
            index: 그룹 행 인덱스.

        Returns:
            None.
        """
        self._pending_selected_index = index

    def sync_views_from_model(self) -> None:
        """모델 내용을 테이블·콘텐츠·포스터 뷰에 다시 반영한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        self._sync_views_from_model()

    def set_rows(self, rows: list[PipelineGroupRow]) -> None:
        """그룹 행을 모델에 설정한다(modelReset으로 뷰 동기화가 이어짐).

        Args:
            self: 이 패널 인스턴스.
            rows: 파이프라인 그룹 행 목록.

        Returns:
            None.
        """
        self._model.set_rows(rows)

    def _sync_header_height(self) -> None:
        """스타일·폰트 변경 후 헤더 고정 높이를 sizeHint 기준으로 다시 맞춘다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        header_h = int(self._header.sizeHint().height())
        if header_h > 0:
            self._header.setFixedHeight(header_h)

    def changeEvent(self, arg__1: QEvent) -> None:
        """폰트·스타일 등 변경 시 헤더 높이를 재계산한다.

        Args:
            self: 이 패널 인스턴스.
            arg__1: Qt 변경 이벤트 (QFrame.changeEvent 시그니처와 동일한 매개변수명).

        Returns:
            None.
        """
        super().changeEvent(arg__1)
        if arg__1.type() in {
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
            QEvent.Type.Polish,
            QEvent.Type.LayoutRequest,
        }:
            self._sync_header_height()
