"""pipeline_result_panel.py

파이프라인 결과 영역: 보기 전환·테이블·콘텐츠·포스터 그리드·상세/미리보기 패널을 통합한다.

Author: Pom Kim
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

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
    VIEW_ICON_L,
    VIEW_ICON_M,
    VIEW_ICON_S,
    VIEW_ICON_XL,
)
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import DetailsPane
from anivault.interfaces.gui.components.organisms.pipeline_table import PipelineTable
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid
from anivault.interfaces.gui.components.organisms.preview_pane import PreviewPane
from anivault.interfaces.gui.models import (
    PipelineGroupRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_group_display_image_url,
    pipeline_row_ready_for_plan,
)
from anivault.interfaces.gui.services.image_loader import ImageLoader
from anivault.interfaces.gui.templates.pipeline_result_ui_state import (
    VIEW_TO_INDEX,
    load_normalized_pipeline_ui_state_from_settings,
    persist_pipeline_results_ui_state,
    restore_pipeline_result_panel_ui_state,
)
from anivault.interfaces.gui.templates.pipeline_selection_sync import (
    on_split_table_selection,
    sync_split_tables_selection,
)
from anivault.interfaces.gui.templates.poster_view_binder import PosterViewBinder

ICON_SIZES = {VIEW_ICON_XL: 220, VIEW_ICON_L: 180, VIEW_ICON_M: 140, VIEW_ICON_S: 100}


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
        self._pane_mode: str | None = None  # "details" | "preview" | None
        self._restoring_state = False
        self._pending_selected_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view_bar = ViewToggleBar()
        self._header = PanelHeader(
            "Pipeline Result",
            "테이블·내용·아이콘 그리드로 결과를 볼 수 있습니다. 보기에서 레이아웃을 선택하세요.",
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

        # 0: Details — TMDB 준비됨 / 미준비 세로 분할 테이블
        self._matched_model = PipelineTableModel()
        self._unmatched_model = PipelineTableModel()
        self._matched_table = PipelineTable(show_header=False, model=self._matched_model)
        self._unmatched_table = PipelineTable(show_header=False, model=self._unmatched_model)
        self._matched_table.selection_changed.connect(
            lambda r: on_split_table_selection(
                "matched",
                r,
                self._rows,
                self._matched_model,
                self._unmatched_model,
                self._apply_unified_selection,
            )
        )
        self._unmatched_table.selection_changed.connect(
            lambda r: on_split_table_selection(
                "unmatched",
                r,
                self._rows,
                self._matched_model,
                self._unmatched_model,
                self._apply_unified_selection,
            )
        )
        details_splitter = QSplitter(Qt.Orientation.Vertical)
        details_splitter.setChildrenCollapsible(False)
        top_wrap = QWidget()
        top_l = QVBoxLayout(top_wrap)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.setSpacing(4)
        _lbl_m = QLabel("TMDB 매칭됨")
        top_l.addWidget(_lbl_m)
        top_l.addWidget(self._matched_table, 1)
        bottom_wrap = QWidget()
        bottom_l = QVBoxLayout(bottom_wrap)
        bottom_l.setContentsMargins(0, 0, 0, 0)
        bottom_l.setSpacing(4)
        _lbl_u = QLabel("미매칭·미진행")
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

        # Right pane placeholder (DetailsPane or PreviewPane)
        self._pane_stack = QStackedWidget()
        self._pane_stack.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        )
        self._pane_stack.setMinimumHeight(0)
        self._pane_stack.addWidget(QWidget())  # empty
        self._details_pane = DetailsPane()
        self._preview_pane = PreviewPane()
        self._image_loader = ImageLoader(self)
        self._poster_binder = PosterViewBinder(self._image_loader, self._preview_pane)
        self._pane_stack.addWidget(self._details_pane)
        self._pane_stack.addWidget(self._preview_pane)
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
        self._view_bar.details_pane_changed.connect(self._on_details_pane)
        self._view_bar.preview_pane_changed.connect(self._on_preview_pane)

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
        combined = list(self._content_view.poster_cards())
        combined.extend(grid_cards)
        self._poster_binder.refresh_poster_pixmaps(combined)
        self._persist_ui_state()

    def _apply_unified_selection(self, index: int) -> None:
        """통합 그룹 인덱스로 상세·미리보기·분할 테이블 선택을 맞춘다.

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
        self._preview_pane.set_row(row)
        self._poster_binder.schedule_preview_image(row)
        sync_split_tables_selection(
            self._rows,
            index,
            self._matched_model,
            self._unmatched_model,
            self._matched_table,
            self._unmatched_table,
        )
        self._persist_ui_state()

    def _on_selection(self, index: int) -> None:
        """선택 인덱스를 반영하고 상세·미리보기 패널과 외부 시그널을 갱신한다.

        Args:
            self: 이 패널 인스턴스.
            index: 그룹 행 인덱스. 범위 밖이면 빈 선택.

        Returns:
            None.
        """
        self._apply_unified_selection(index)

    def _ensure_details_pane_visible(self) -> None:
        """세부 정보 창이 꺼져 있으면 토글 ON과 동일하게 우측 패널을 연다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        if not self._view_bar.details_pane_checked():
            self._view_bar.set_details_pane_checked(True)
            self._on_details_pane(True)

    def _on_icon_grid_card_clicked(self, index: int) -> None:
        """아이콘 카드 클릭: 동일 행+세부 패널 표시 중이면 닫고, 아니면 열고 선택한다.

        Args:
            self: 이 패널 인스턴스.
            index: 그룹 행 인덱스.

        Returns:
            None.
        """
        if (
            self._view_bar.details_pane_checked()
            and self._pane_mode == "details"
            and self._selected_index == index
        ):
            self._view_bar.set_details_pane_checked(False)
            self._on_details_pane(False)
            return
        self._ensure_details_pane_visible()
        self._on_selection(index)

    def _on_details_pane(self, checked: bool) -> None:
        """상세 패널 토글에 따라 우측 스택·스플리터 크기를 조정한다.

        Args:
            self: 이 패널 인스턴스.
            checked: 상세 패널 표시 여부.

        Returns:
            None.
        """
        if checked:
            self._pane_mode = "details"
            self._pane_stack.setCurrentIndex(1)
            w = self._main_splitter.width()
            self._main_splitter.setSizes(
                [max(self._main_min_width, w - self._pane_width), self._pane_width]
            )
        else:
            # If both toggles are on, turning off the inactive one should not hide the
            # currently displayed pane.
            if self._pane_mode == "details":
                if self._view_bar.preview_pane_checked():
                    self._pane_mode = "preview"
                    self._pane_stack.setCurrentIndex(2)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes(
                        [max(self._main_min_width, w - self._pane_width), self._pane_width]
                    )
                else:
                    self._pane_mode = None
                    self._pane_stack.setCurrentIndex(0)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes([w, 0])
        self._persist_ui_state()

    def _on_preview_pane(self, checked: bool) -> None:
        """미리보기 패널 토글에 따라 우측 스택·스플리터 크기를 조정한다.

        Args:
            self: 이 패널 인스턴스.
            checked: 미리보기 패널 표시 여부.

        Returns:
            None.
        """
        if checked:
            self._pane_mode = "preview"
            self._pane_stack.setCurrentIndex(2)
            w = self._main_splitter.width()
            self._main_splitter.setSizes(
                [max(self._main_min_width, w - self._pane_width), self._pane_width]
            )
        else:
            if self._pane_mode == "preview":
                if self._view_bar.details_pane_checked():
                    self._pane_mode = "details"
                    self._pane_stack.setCurrentIndex(1)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes(
                        [max(self._main_min_width, w - self._pane_width), self._pane_width]
                    )
                else:
                    self._pane_mode = None
                    self._pane_stack.setCurrentIndex(0)
                    w = self._main_splitter.width()
                    self._main_splitter.setSizes([w, 0])
        self._persist_ui_state()

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

        card.mousePressEvent = _on_press  # type: ignore[method-assign]

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
                    image_url=pipeline_group_display_image_url(g),
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
        self._poster_binder.refresh_poster_pixmaps(all_poster_cards)
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
        restore_pipeline_result_panel_ui_state(
            load_normalized_pipeline_ui_state_from_settings(),
            set_restoring=lambda v: setattr(self, "_restoring_state", v),
            set_pending_selected_index=lambda i: setattr(self, "_pending_selected_index", i),
            apply_view_key=self._on_view_changed,
            apply_details_pane=self._on_details_pane,
            apply_preview_pane=self._on_preview_pane,
        )

    def _persist_ui_state(self) -> None:
        """현재 Pipeline Result UI 상태를 설정 저장소에 기록한다.

        Args:
            self: 이 패널 인스턴스.

        Returns:
            None.
        """
        persist_pipeline_results_ui_state(
            view_key=self._view_bar.current_view(),
            details_pane=self._view_bar.details_pane_checked(),
            preview_pane=self._view_bar.preview_pane_checked(),
            selected_index=self._selected_index,
            skip_if_restoring=self._restoring_state,
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
            arg__1: Qt 변경 이벤트(PySide 스텁 시그니처와 이름 일치).

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
