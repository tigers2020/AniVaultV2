"""Dialog showing TMDB season episodes and local file coverage."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QMouseEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from anivault.interfaces.gui import theme
from anivault.interfaces.gui.components.atoms.rounded_pixmap_label import RoundedPixmapLabel
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.models.episode_overview import EpisodeSlotViewModel
from anivault.interfaces.gui.services.image_loader import ImageLoader

_GRID_COLUMNS = 4
_EPISODE_IMAGE_HEIGHT = 96


class _EpisodeSlotCard(QFrame):
    """Compact episode slot card that can open a local file on double click."""

    def __init__(self, slot: EpisodeSlotViewModel, parent=None) -> None:
        super().__init__(parent)
        self._slot = slot
        self._overlay: QFrame | None = None
        self.setObjectName("episode_overview_slot_card")
        self.setMinimumHeight(170)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if not slot.missing and slot.file_path
            else Qt.CursorShape.ArrowCursor
        )
        self.setStyleSheet("""
            QFrame#episode_overview_slot_card {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
            """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        self._image_label = RoundedPixmapLabel(self)
        self._image_label.setFixedHeight(_EPISODE_IMAGE_HEIGHT)
        self._image_label.set_placeholder_text("")
        number_label = QLabel(translate(K.DLG_EP_OVERVIEW_EPISODE, number=slot.number))
        number_label.setStyleSheet("font-weight: 700;")
        title_label = QLabel(slot.title or translate(K.DLG_EP_OVERVIEW_UNTITLED))
        title_label.setWordWrap(True)

        layout.addWidget(self._image_label)
        layout.addWidget(number_label)
        layout.addWidget(title_label)

        if slot.missing:
            overlay = QFrame(self)
            overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            overlay.setStyleSheet("background: rgba(220, 38, 38, 0.28); border-radius: 12px;")
            overlay.setGeometry(self.rect())
            overlay.raise_()
            self._overlay = overlay

    @property
    def image_url(self) -> str:
        return self._slot.image_url

    def set_image_pixmap(self, pixmap) -> None:
        self._image_label.set_source_pixmap(pixmap)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._overlay is not None:
            self._overlay.setGeometry(self.rect())

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        file_path = self._slot.file_path
        if event.button() == Qt.MouseButton.LeftButton and file_path and Path(file_path).is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class EpisodeOverviewDialog(QDialog):
    """Episode overview dialog with loading and slot grid states."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._series_title = ""
        self._season_number = 0
        self._cards_by_image_url: dict[str, list[_EpisodeSlotCard]] = {}
        self._image_loader = ImageLoader(self)
        self._image_loader.loaded.connect(self._on_image_loaded)
        self.setMinimumSize(720, 520)
        self.setStyleSheet(theme.card_panel())

        layout = QVBoxLayout(self)
        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(theme.scroll_area_transparent())
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(theme.compact_gap_px())
        scroll.setWidget(self._grid_host)
        layout.addWidget(scroll, 1)

        self.retranslate_ui()
        get_i18n_service().language_changed.connect(self.retranslate_ui)

    def set_context(self, series_title: str, season_number: int) -> None:
        self._series_title = (series_title or "").strip()
        self._season_number = season_number
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        title = self._series_title or translate(K.DLG_EP_OVERVIEW_FALLBACK_TITLE)
        self.setWindowTitle(
            translate(
                K.DLG_EP_OVERVIEW_TITLE,
                title=title,
                season_number=self._season_number,
            )
        )
        if not self._status_label.text():
            self._status_label.setText(translate(K.DLG_EP_OVERVIEW_LOADING))

    def show_loading(self) -> None:
        self._clear_grid()
        self._status_label.setText(translate(K.DLG_EP_OVERVIEW_LOADING))

    def show_empty(self) -> None:
        self._clear_grid()
        self._status_label.setText(translate(K.DLG_EP_OVERVIEW_EMPTY))

    def show_slots(self, slots: list[EpisodeSlotViewModel]) -> None:
        self._clear_grid()
        if not slots:
            self.show_empty()
            return
        self._status_label.setText(translate(K.DLG_EP_OVERVIEW_SUMMARY, count=len(slots)))
        for index, slot in enumerate(slots):
            row = index // _GRID_COLUMNS
            col = index % _GRID_COLUMNS
            card = _EpisodeSlotCard(slot)
            self._grid.addWidget(card, row, col)
            if card.image_url:
                self._cards_by_image_url.setdefault(card.image_url, []).append(card)
        for col in range(_GRID_COLUMNS):
            self._grid.setColumnStretch(col, 1)
        self._refresh_slot_images()

    def _clear_grid(self) -> None:
        self._cards_by_image_url.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_slot_images(self) -> None:
        for image_url, cards in self._cards_by_image_url.items():
            pixmap = self._image_loader.get(image_url)
            if pixmap is not None:
                for card in cards:
                    card.set_image_pixmap(pixmap)
                continue
            self._image_loader.load(image_url)

    def _on_image_loaded(self, image_url: str, pixmap) -> None:
        for card in self._cards_by_image_url.get(image_url, []):
            card.set_image_pixmap(pixmap)
