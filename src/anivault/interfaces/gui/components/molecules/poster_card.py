"""poster_card.py

이미지 영역 + 제목 + 메타 + 경로. 포스터 2:3 또는 백드롭 5:2 비율.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label, RoundedPixmapLabel
from anivault.interfaces.gui.components.molecules.path_box import PathBox

# Image area height/width: poster portrait 2:3; backdrop wide 5:2 (width:height)
POSTER_IMAGE_ASPECT_HW = 3 / 2
BACKDROP_IMAGE_ASPECT_HW = 2 / 5
# Space for title + meta (+ path on non-compact) below the image
COMPACT_BODY_HEIGHT_PX = 48
COMPACT_TITLE_ONLY_BODY_HEIGHT_PX = 28
NON_COMPACT_BODY_HEIGHT_PX = 100
# Vertical gap between image row and title/meta row (must match layout.setSpacing)
CARD_LAYOUT_SPACING_COMPACT_PX = 6
CARD_LAYOUT_SPACING_POSTER_PX = 8


class PosterCard(QFrame):
    """포스터 한 장: 이미지 슬롯, 제목, 메타, 경로(비컴팩트)."""

    def __init__(
        self,
        title: str = "",
        meta: str = "",
        path: str = "",
        image_url: str = "",
        parent=None,
        variant: Literal["poster", "compact"] = "poster",
        image_aspect: Literal["poster", "backdrop"] = "poster",
        text_panel_overlay: bool = False,
        title_only: bool = False,
    ):
        """레이아웃·최소 크기·자식 위젯을 구성한다.

        Args:
            self: 이 위젯.
            title: 카드 제목.
            meta: 메타 한 줄.
            path: 경로(PathBox, 비컴팩트만).
            image_url: 비동기 로드용 URL(내부 보관).
            parent: 부모 위젯(선택).
            variant: poster | compact.
            image_aspect: poster | backdrop 비율.
            text_panel_overlay: 컴팩트일 때 텍스트 패널 오버레이 여부.
            title_only: compact일 때 제목만 표시(메타 생략). poster에서는 무시.

        Returns:
            None.
        """
        super().__init__(parent)
        is_compact = variant == "compact"
        use_text_panel = is_compact and text_panel_overlay
        self._is_compact = is_compact
        self._title_only = bool(title_only and is_compact)
        self._aspect_hw_compact = (
            POSTER_IMAGE_ASPECT_HW if image_aspect == "poster" else BACKDROP_IMAGE_ASPECT_HW
        )
        self.setStyleSheet(theme.poster_card())
        self._set_minimum_size(is_compact)
        sp = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Clear gap between image slot and title/meta (no stretch on rows = no shared slack)
        layout.setSpacing(
            CARD_LAYOUT_SPACING_COMPACT_PX if is_compact else CARD_LAYOUT_SPACING_POSTER_PX
        )
        self._img_placeholder = "Backdrop" if image_aspect == "backdrop" else "Poster"
        self._setup_image_row(layout)
        body, body_frame = self._create_body_layout(use_text_panel, is_compact)
        self._populate_body(body, title, meta, path, is_compact, self._title_only)
        self._attach_body_to_main(layout, body, body_frame, use_text_panel)
        layout.addStretch(1)
        self._image_url = image_url

    def _set_minimum_size(self, is_compact: bool) -> None:
        """컴팩트/포스터에 맞는 최소 너비·높이를 설정한다.

        Args:
            self: 이 위젯.
            is_compact: 컴팩트 카드 여부.

        Returns:
            None.
        """
        if is_compact:
            body_px = (
                COMPACT_TITLE_ONLY_BODY_HEIGHT_PX if self._title_only else COMPACT_BODY_HEIGHT_PX
            )
            self.setMinimumWidth(120)
            self.setMinimumHeight(
                int(120 * self._aspect_hw_compact) + CARD_LAYOUT_SPACING_COMPACT_PX + body_px,
            )
            return
        self.setMinimumWidth(140)
        self.setMinimumHeight(
            int(140 * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX,
        )

    def _create_body_layout(
        self, use_text_panel: bool, is_compact: bool
    ) -> tuple[QVBoxLayout, QFrame | None]:
        """본문용 세로 레이아웃과 선택적 프레임을 만든다.

        Args:
            self: 이 위젯.
            use_text_panel: 오버레이 패널 프레임 사용 여부.
            is_compact: 컴팩트 여부(여백·간격).

        Returns:
            (body 레이아웃, 패널 프레임 또는 None).
        """
        if use_text_panel:
            body_frame = QFrame()
            body_frame.setObjectName("content_view_text_panel")
            body_frame.setStyleSheet(theme.content_view_text_panel_overlay())
            body = QVBoxLayout(body_frame)
            body.setSpacing(2)
            body.setContentsMargins(6, 6, 6, 6)
            return body, body_frame
        body = QVBoxLayout()
        body.setSpacing(2 if is_compact else 6)
        body.setContentsMargins(
            4 if is_compact else 10,
            0 if is_compact else 10,
            4 if is_compact else 10,
            2 if is_compact else 10,
        )
        return body, None

    def _setup_image_row(self, layout: QVBoxLayout) -> None:
        """이미지 슬롯 위젯을 메인 레이아웃에 넣는다.

        Args:
            self: 이 위젯.
            layout: 메인 세로 레이아웃.

        Returns:
            None.
        """
        self._img_label = RoundedPixmapLabel()
        self._img_label.setMinimumHeight(0)
        self._img_label.set_placeholder_text(self._img_placeholder)
        self._img_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(self._img_label, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)

    def _populate_body(
        self,
        body: QVBoxLayout,
        title: str,
        meta: str,
        path: str,
        is_compact: bool,
        title_only: bool,
    ) -> None:
        """제목·메타·경로 라벨을 본문에 채운다.

        Args:
            self: 이 위젯.
            body: 본문 세로 레이아웃.
            title: 제목 문자열.
            meta: 메타 문자열.
            path: 경로 문자열.
            is_compact: 컴팩트면 PathBox 생략.
            title_only: 컴팩트일 때 메타 라벨을 붙이지 않는다.

        Returns:
            None.
        """
        self._title_text = title
        self._meta_text = meta
        self._title_lbl = Label(title, "title")
        self._title_lbl.setWordWrap(not is_compact)
        self._title_lbl.setStyleSheet(theme.poster_card_title())
        body.addWidget(self._title_lbl)

        self._meta_lbl: Label | None
        if is_compact and title_only:
            self._meta_lbl = None
        else:
            meta_lbl = Label(meta, "muted")
            meta_lbl.setWordWrap(not is_compact)
            meta_lbl.setStyleSheet(theme.poster_card_meta())
            body.addWidget(meta_lbl)
            self._meta_lbl = meta_lbl

        self._path_box: PathBox | None = None
        if not is_compact:
            self._path_box = PathBox(path)
            body.addWidget(self._path_box)

    def _attach_body_to_main(
        self,
        layout: QVBoxLayout,
        body: QVBoxLayout,
        body_frame: QFrame | None,
        use_text_panel: bool,
    ) -> None:
        """본문을 메인 레이아웃에 붙인다(패널 프레임 또는 raw layout).

        Args:
            self: 이 위젯.
            layout: 메인 세로 레이아웃.
            body: 본문 레이아웃.
            body_frame: 오버레이일 때 프레임.
            use_text_panel: 프레임 모드 여부.

        Returns:
            None.
        """
        if use_text_panel and body_frame is not None:
            layout.addWidget(body_frame, stretch=0)
            return
        layout.addLayout(body, stretch=0)

    @property
    def image_url(self) -> str:
        """비동기 이미지 로드에 쓸 URL.

        Args:
            self: 이 위젯.

        Returns:
            URL 문자열.
        """
        return self._image_url

    def sizeHint(self) -> QSize:
        """고정 비율 기준 선호 크기를 반환한다.

        Args:
            self: 이 위젯.

        Returns:
            QSize.
        """
        if self._is_compact:
            body_px = (
                COMPACT_TITLE_ONLY_BODY_HEIGHT_PX if self._title_only else COMPACT_BODY_HEIGHT_PX
            )
            w = 140
            return QSize(
                w,
                int(w * self._aspect_hw_compact) + CARD_LAYOUT_SPACING_COMPACT_PX + body_px,
            )
        w = 180
        return QSize(
            w,
            int(w * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX,
        )

    def hasHeightForWidth(self) -> bool:
        """너비에 따른 높이 힌트를 제공한다.

        Args:
            self: 이 위젯.

        Returns:
            True.
        """
        return True

    def heightForWidth(self, arg__1: int) -> int:
        """주어진 너비에서 이미지+본문 높이 합을 계산한다.

        Args:
            self: 이 위젯.
            w: 위젯 너비.

        Returns:
            픽셀 높이.
        """
        if arg__1 <= 0:
            return self.minimumHeight()
        if self._is_compact:
            body_px = (
                COMPACT_TITLE_ONLY_BODY_HEIGHT_PX if self._title_only else COMPACT_BODY_HEIGHT_PX
            )
            return int(arg__1 * self._aspect_hw_compact) + CARD_LAYOUT_SPACING_COMPACT_PX + body_px
        return (
            int(arg__1 * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX
        )

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """이미지 슬롯에 픽스맵을 넣거나 플레이스홀더로 되돌린다.

        Args:
            self: 이 위젯.
            pixmap: 표시할 이미지. None 또는 null이면 클리어.

        Returns:
            None.
        """
        if pixmap is not None and not pixmap.isNull():
            self._img_label.set_source_pixmap(pixmap)
        else:
            self._img_label.clear_source_pixmap()
            self._img_label.set_placeholder_text(self._img_placeholder)

    def set_title(self, title: str) -> None:
        """제목 라벨 텍스트를 바꾼다.

        Args:
            self: 이 위젯.
            title: 새 제목.

        Returns:
            None.
        """
        self._title_text = title
        self._title_lbl.setText(title)

    def resizeEvent(self, event) -> None:
        """너비에 맞춰 이미지 높이·카드 전체 높이·컴팩트 말줄임을 갱신한다.

        Args:
            self: 이 위젯.
            event: Qt 리사이즈 이벤트.

        Returns:
            None.
        """
        super().resizeEvent(event)
        w = self.width()
        if w > 0:
            aspect = self._aspect_hw_compact if self._is_compact else POSTER_IMAGE_ASPECT_HW
            img_h = int(w * aspect)
            self._img_label.setFixedHeight(img_h)
            self._img_label.setMaximumHeight(img_h)
            # QVBoxLayout in QScrollArea does not always re-apply heightForWidth when width
            # changes; lock total height so image + body track width at fixed ratio.
            target_h = self.heightForWidth(w)
            if self.height() != target_h:
                self.setFixedHeight(target_h)
                self.updateGeometry()
        if self._is_compact:
            self._apply_compact_elide()

    def _apply_compact_elide(self) -> None:
        """컴팩트 모드에서 제목·메타를 한 줄 말줄임한다.

        Args:
            self: 이 위젯.

        Returns:
            None.
        """
        pairs: list[tuple[Label, str]] = [(self._title_lbl, self._title_text)]
        if self._meta_lbl is not None:
            pairs.append((self._meta_lbl, self._meta_text))
        for lbl, raw_text in pairs:
            metrics = QFontMetrics(lbl.font())
            available = max(0, lbl.width() - 2)
            if available > 0 and raw_text:
                lbl.setText(metrics.elidedText(raw_text, Qt.TextElideMode.ElideRight, available))

    def set_path(self, path: str) -> None:
        """PathBox가 있으면 경로를 갱신한다.

        Args:
            self: 이 위젯.
            path: 새 경로.

        Returns:
            None.
        """
        if self._path_box is not None:
            self._path_box.set_path(path)
