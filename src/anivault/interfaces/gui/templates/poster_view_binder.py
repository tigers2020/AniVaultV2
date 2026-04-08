"""poster_view_binder.py

ImageLoader와 포스터 카드·미리보기 패널 픽스맵 바인딩(상태 최소화).

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from PySide6.QtGui import QPixmap

from anivault.interfaces.gui.models import PipelineGroupRow, pipeline_group_display_image_url
from anivault.interfaces.gui.services.image_loader import ImageLoader


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


class _PreviewTarget(Protocol):
    """미리보기 패널이 제공해야 하는 최소 계약."""

    def set_pixmap(self, pixmap: QPixmap | None) -> None:
        """미리보기 이미지 픽스맵을 반영한다."""
        ...


class PosterViewBinder:
    """포스터 대상 목록과 미리보기 패널을 ``ImageLoader``에 연결한다."""

    def __init__(self, image_loader: ImageLoader, preview_pane: _PreviewTarget) -> None:
        """로더·미리보기 참조를 저장하고 ``loaded`` 시그널을 연결한다.

        Args:
            self: 이 바인더 인스턴스.
            image_loader: 비동기 이미지 로더(부모는 보통 패널).
            preview_pane: 미리보기 픽스맵 대상.

        Returns:
            None.
        """
        self._image_loader = image_loader
        self._preview_pane = preview_pane
        self._cards_by_url: dict[str, list[_ImageRowTarget]] = {}
        self._preview_pending_url: str | None = None
        image_loader.loaded.connect(self._on_poster_image_loaded)

    def _on_poster_image_loaded(self, url: str, pixmap: QPixmap) -> None:
        """로드 완료 시 URL에 매핑된 카드와 대기 중인 미리보기를 갱신한다.

        Args:
            self: 이 바인더 인스턴스.
            url: 로드된 이미지 URL.
            pixmap: 디코딩된 픽스맵.

        Returns:
            None.
        """
        for card in self._cards_by_url.get(url, []):
            card.set_pixmap(pixmap if not pixmap.isNull() else None)
        if self._preview_pending_url == url:
            self._preview_pane.set_pixmap(pixmap if not pixmap.isNull() else None)
            self._preview_pending_url = None

    def schedule_preview_image(self, row: PipelineGroupRow | None) -> None:
        """선택 그룹의 포스터를 미리보기 패널에 캐시 또는 비동기로 반영한다.

        Args:
            self: 이 바인더 인스턴스.
            row: 선택 그룹. None이면 대기 URL만 해제.

        Returns:
            None.
        """
        self._preview_pending_url = None
        if row is None:
            return
        img_url = pipeline_group_display_image_url(row).strip()
        if not img_url:
            return
        self._preview_pending_url = img_url
        cached = self._image_loader.get(img_url)
        if cached is not None:
            self._preview_pane.set_pixmap(cached)
            self._preview_pending_url = None
            return
        self._image_loader.load(img_url)

    def refresh_poster_pixmaps(self, cards: Sequence[_ImageRowTarget]) -> None:
        """카드 목록의 URL을 수집해 캐시 히트는 즉시 반영하고 나머지는 로드한다.

        Args:
            self: 이 바인더 인스턴스.
            cards: 갱신할 포스터 카드(또는 동일 계약) 목록.

        Returns:
            None.
        """
        self._cards_by_url.clear()
        for card in cards:
            u = (card.image_url or "").strip()
            if not u:
                continue
            self._cards_by_url.setdefault(u, []).append(card)
        for url in self._cards_by_url:
            cached = self._image_loader.get(url)
            if cached is not None:
                for c in self._cards_by_url[url]:
                    c.set_pixmap(cached)
            else:
                self._image_loader.load(url)
