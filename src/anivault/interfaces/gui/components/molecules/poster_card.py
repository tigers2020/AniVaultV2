"""Poster card: image + title + meta + path. Image via loader/placeholder. Portrait 2:3 ratio."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
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
    ):
        super().__init__(parent)
        self.setStyleSheet(theme.poster_card())
        self.setMinimumWidth(120)
        self.setMinimumHeight(int(120 * POSTER_ASPECT))
        # Height follows width (portrait 2:3) so layout can align rows
        sp = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._img_label = QLabel()
        self._img_label.setMinimumHeight(120)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setStyleSheet(theme.poster_card_image())
        self._img_label.setText("Poster")
        self._img_label.setScaledContents(False)
        self._img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Picture area gets 3/4 of card height; labels stay in bottom 1/4
        layout.addWidget(self._img_label, 3)
        body = QVBoxLayout()
        body.setSpacing(6)
        body.setContentsMargins(10, 10, 10, 10)
        title_lbl = Label(title, "title")
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(theme.poster_card_title())
        body.addWidget(title_lbl)
        meta_lbl = Label(meta, "muted")
        meta_lbl.setWordWrap(True)
        meta_lbl.setStyleSheet(theme.poster_card_meta())
        body.addWidget(meta_lbl)
        self._path_box = PathBox(path)
        body.addWidget(self._path_box)
        layout.addLayout(body, 1)
        self._image_url = image_url

    def sizeHint(self) -> QSize:
        w = 160
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
        layout = self.layout()
        if layout and layout.count() >= 2:
            inner = layout.itemAt(1).layout()
            if inner and inner.count():
                inner.itemAt(0).widget().setText(title)

    def set_path(self, path: str) -> None:
        self._path_box.set_path(path)
