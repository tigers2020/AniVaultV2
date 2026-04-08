"""image_loader.py

포스터 URL 비동기 로드. 메모리 캐시·실패 시 빈 QPixmap.

Author: Pom Kim
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

# Policy: memory cache first; if present show immediately; else placeholder then async load; on failure keep fallback.


class ImageLoader(QObject):
    """URL로 이미지를 받아 loaded 시그널로 pixmap을 보낸다."""

    loaded = Signal(str, QPixmap)  # url, pixmap (empty on failure)

    def __init__(self, parent=None):
        """QNetworkAccessManager와 캐시·pending 맵을 초기화한다.

        Args:
            self: 이 로더.
            parent: Qt 부모.

        Returns:
            None.
        """
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)
        self._nam.finished.connect(self._on_finished)
        self._cache: dict[str, QPixmap] = {}
        self._pending: dict[QNetworkReply, str] = {}
        self._inflight_urls: set[str] = set()

    def get(self, url: str) -> QPixmap | None:
        """캐시에 있으면 pixmap을, 없으면 None을 반환한다.

        Args:
            self: 이 로더.
            url: 이미지 URL.

        Returns:
            캐시된 pixmap 또는 None.
        """
        return self._cache.get(url)

    def load(self, url: str) -> None:
        """캐시 히트면 즉시 emit하고, 로컬·file URL은 동기 로드, http(s)는 GET한다.

        Args:
            self: 이 로더.
            url: http(s), file URL, 또는 절대 로컬 경로.

        Returns:
            None.
        """
        u = (url or "").strip()
        if not u:
            return
        if u in self._cache:
            self.loaded.emit(u, self._cache[u])
            return
        if self._load_local(u):
            return
        self._load_remote(u)

    def _emit_local_pixmap(self, cache_key: str, pixmap: QPixmap) -> None:
        """로컬에서 읽은 pixmap을 캐시하고 emit한다."""
        if not pixmap.isNull():
            self._cache[cache_key] = pixmap
            self.loaded.emit(cache_key, pixmap)
            return
        self.loaded.emit(cache_key, QPixmap())

    def _load_local(self, url: str) -> bool:
        """file URL/절대 경로를 동기 로드하고 처리 여부를 반환한다."""
        if url.startswith("file:"):
            local = QUrl(url).toLocalFile()
            pix = QPixmap(local) if local else QPixmap()
            self._emit_local_pixmap(url, pix)
            return True

        try:
            path = Path(url)
        except OSError:
            return False

        if not (path.is_absolute() and path.is_file()):
            return False

        self._emit_local_pixmap(url, QPixmap(str(path)))
        return True

    def _load_remote(self, url: str) -> None:
        """http(s) URL만 비동기 요청한다."""
        if not url.startswith("http") or url in self._inflight_urls:
            return

        self._inflight_urls.add(url)
        request = QNetworkRequest(QUrl(url))
        reply = self._nam.get(request)
        self._pending[reply] = url

    def _on_finished(self, reply: QNetworkReply) -> None:
        """응답을 pixmap으로 디코딩해 캐시·emit한다.

        Args:
            self: 이 로더.
            reply: 완료된 QNetworkReply.

        Returns:
            None.
        """
        url = self._pending.pop(reply, None)
        if url is None:
            return
        self._inflight_urls.discard(url)
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
