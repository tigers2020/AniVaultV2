"""Poster card: image + title + meta + path. Image area matches poster (2:3) or backdrop (5:2)."""

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
NON_COMPACT_BODY_HEIGHT_PX = 100
# Vertical gap between image row and title/meta row (must match layout.setSpacing)
CARD_LAYOUT_SPACING_COMPACT_PX = 6
CARD_LAYOUT_SPACING_POSTER_PX = 8


class PosterCard(QFrame):
    """Single poster: image area, title, meta line, path box."""

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
    ):
        super().__init__(parent)
        is_compact = variant == "compact"
        use_text_panel = is_compact and text_panel_overlay
        self._is_compact = is_compact
        self._aspect_hw_compact = (
            POSTER_IMAGE_ASPECT_HW if image_aspect == "poster" else BACKDROP_IMAGE_ASPECT_HW
        )
        self.setStyleSheet(theme.poster_card())
        if is_compact:
            self.setMinimumWidth(120)
            self.setMinimumHeight(
                int(120 * self._aspect_hw_compact)
                + CARD_LAYOUT_SPACING_COMPACT_PX
                + COMPACT_BODY_HEIGHT_PX
            )
        else:
            self.setMinimumWidth(140)
            self.setMinimumHeight(
                int(140 * POSTER_IMAGE_ASPECT_HW)
                + CARD_LAYOUT_SPACING_POSTER_PX
                + NON_COMPACT_BODY_HEIGHT_PX
            )
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
        self._img_label = RoundedPixmapLabel()
        self._img_label.setMinimumHeight(0)
        self._img_label.set_placeholder_text(self._img_placeholder)
        self._img_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(self._img_label, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)
        body_frame: QFrame | None = None
        if use_text_panel:
            body_frame = QFrame()
            body_frame.setObjectName("content_view_text_panel")
            body_frame.setStyleSheet(theme.content_view_text_panel_overlay())
            body = QVBoxLayout(body_frame)
            body.setSpacing(2)
            body.setContentsMargins(6, 6, 6, 6)
        else:
            body = QVBoxLayout()
            body.setSpacing(2 if is_compact else 6)
            body.setContentsMargins(
                4 if is_compact else 10,
                0 if is_compact else 10,
                4 if is_compact else 10,
                2 if is_compact else 10,
            )
        self._title_text = title
        self._meta_text = meta
        self._title_lbl = Label(self._title_text, "title")
        title_lbl = self._title_lbl
        title_lbl.setWordWrap(True)
        if is_compact:
            title_lbl.setWordWrap(False)
        title_lbl.setStyleSheet(theme.poster_card_title())
        body.addWidget(title_lbl)
        self._meta_lbl = Label(self._meta_text, "muted")
        meta_lbl = self._meta_lbl
        meta_lbl.setWordWrap(True)
        if is_compact:
            meta_lbl.setWordWrap(False)
        meta_lbl.setStyleSheet(theme.poster_card_meta())
        body.addWidget(meta_lbl)
        self._path_box: PathBox | None = None
        if not is_compact:
            self._path_box = PathBox(path)
            body.addWidget(self._path_box)
        if use_text_panel and body_frame is not None:
            layout.addWidget(body_frame, stretch=0)
        else:
            layout.addLayout(body, stretch=0)
        layout.addStretch(1)
        self._image_url = image_url

    @property
    def image_url(self) -> str:
        return self._image_url

    def sizeHint(self) -> QSize:
        if self._is_compact:
            w = 140
            return QSize(
                w,
                int(w * self._aspect_hw_compact)
                + CARD_LAYOUT_SPACING_COMPACT_PX
                + COMPACT_BODY_HEIGHT_PX,
            )
        w = 180
        return QSize(
            w,
            int(w * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX,
        )

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        if w <= 0:
            return self.minimumHeight()
        if self._is_compact:
            return (
                int(w * self._aspect_hw_compact)
                + CARD_LAYOUT_SPACING_COMPACT_PX
                + COMPACT_BODY_HEIGHT_PX
            )
        return (
            int(w * POSTER_IMAGE_ASPECT_HW)
            + CARD_LAYOUT_SPACING_POSTER_PX
            + NON_COMPACT_BODY_HEIGHT_PX
        )

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self._img_label.set_source_pixmap(pixmap)
        else:
            self._img_label.clear_source_pixmap()
            self._img_label.set_placeholder_text(self._img_placeholder)

    def set_title(self, title: str) -> None:
        self._title_text = title
        self._title_lbl.setText(title)

    def resizeEvent(self, event) -> None:
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
        pairs = (
            (self._title_lbl, self._title_text),
            (self._meta_lbl, self._meta_text),
        )
        for lbl, raw_text in pairs:
            metrics = QFontMetrics(lbl.font())
            available = max(0, lbl.width() - 2)
            if available > 0 and raw_text:
                lbl.setText(metrics.elidedText(raw_text, Qt.TextElideMode.ElideRight, available))

    def set_path(self, path: str) -> None:
        if self._path_box is not None:
            self._path_box.set_path(path)
