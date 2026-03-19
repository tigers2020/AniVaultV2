"""Poster card: image + title + meta + path. Image via loader/placeholder. Portrait 2:3 ratio."""

from typing import Literal

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFontMetrics, QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms import Label
from anivault.interfaces.gui.components.molecules import PathBox

# Portrait poster ratio: width : height = 2 : 3
POSTER_ASPECT = 3 / 2  # height / width


class PosterCard(QFrame):
    """Single poster: image area, title, meta line, path box. Keeps portrait ratio 2:3."""

    def __init__(
        self,
        title: str = "",
        meta: str = "",
        path: str = "",
        image_url: str = "",
        parent=None,
        variant: Literal["poster", "compact"] = "poster",
    ):
        super().__init__(parent)
        is_compact = variant == "compact"
        self._is_compact = is_compact
        self.setStyleSheet(theme.poster_card())
        if is_compact:
            self.setMinimumWidth(120)
            self.setMinimumHeight(88)
        else:
            self.setMinimumWidth(140)
            self.setMinimumHeight(int(140 * POSTER_ASPECT))
        # Height follows width (portrait 2:3) so layout can align rows
        sp = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._img_label = QLabel()
        # In compact mode, children minimum sizes must not exceed the card's fixed height.
        if is_compact:
            self._img_label.setMinimumHeight(0)
        else:
            self._img_label.setMinimumHeight(140)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setStyleSheet(theme.poster_card_image())
        self._img_label.setText("Poster")
        self._img_label.setScaledContents(False)
        self._img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Picture area gets 3/4 of card height; labels stay in bottom 1/4
        layout.addWidget(self._img_label, 4 if is_compact else 3)
        body = QVBoxLayout()
        body.setSpacing(2 if is_compact else 6)
        body.setContentsMargins(
            4 if is_compact else 10,
            2 if is_compact else 10,
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
        layout.addLayout(body, 1)
        self._image_url = image_url

    def sizeHint(self) -> QSize:
        w = 140 if self._is_compact else 180
        return QSize(w, int(w * POSTER_ASPECT))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, w: int) -> int:
        return int(w * POSTER_ASPECT) if w > 0 else self.minimumHeight()

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        if pixmap is not None and not pixmap.isNull():
            self._img_label.setPixmap(
                pixmap.scaled(
                    self._img_label.width(),
                    self._img_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self._img_label.clear()
            self._img_label.setText("Poster")

    def set_title(self, title: str) -> None:
        self._title_text = title
        self._title_lbl.setText(title)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not self._is_compact:
            return
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
