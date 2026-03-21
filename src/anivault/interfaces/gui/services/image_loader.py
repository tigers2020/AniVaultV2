"""image_loader.py

포스터 URL 비동기 로드. 메모리 캐시·실패 시 빈 QPixmap.

Author: Pom Kim
"""

from __future__ import annotations

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
        """캐시 히트면 즉시 emit하고, 아니면 GET 요청을 시작한다.

        Args:
            self: 이 로더.
            url: http(s) URL.

        Returns:
            None.
        """
        if not url or not url.startswith("http"):
            return
        if url in self._cache:
            self.loaded.emit(url, self._cache[url])
            return
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
