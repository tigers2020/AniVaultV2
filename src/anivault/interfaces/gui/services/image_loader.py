"""Async poster image loading. Memory cache; placeholder then load; fallback on failure."""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

# Policy: memory cache first; if present show immediately; else placeholder then async load; on failure keep fallback.


class ImageLoader(QObject):
    """Load images by URL; emit pixmap when done. Cache in memory."""

    loaded = Signal(str, QPixmap)  # url, pixmap (empty on failure)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_finished)
        self._cache: dict[str, QPixmap] = {}
        self._pending: dict[QNetworkReply, str] = {}

    def get(self, url: str) -> QPixmap | None:
        """Return cached pixmap if available, else None (caller shows placeholder)."""
        return self._cache.get(url)

    def load(self, url: str) -> None:
        """If cached, emit loaded immediately. Else start network request."""
        if not url or not url.startswith("http"):
            return
        if url in self._cache:
            self.loaded.emit(url, self._cache[url])
            return
        request = QNetworkRequest(QUrl(url))
        reply = self._nam.get(request)
        self._pending[reply] = url

    def _on_finished(self, reply: QNetworkReply) -> None:
        url = self._pending.pop(reply, None)
        if url is None:
            return
        reply.deleteLater()
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.loaded.emit(url, QPixmap())
            return
        data = reply.readAll()
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            self._cache[url] = pixmap
            self.loaded.emit(url, pixmap)
        else:
            self.loaded.emit(url, QPixmap())
