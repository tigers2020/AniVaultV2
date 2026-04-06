"""client.py

tmdbapis를 통한 TMDB HTTP 접근. 이 어댑터 패키지 내부에서만 사용한다.

환경 변수 ``ANIVAULT_TMDB_MIN_INTERVAL``(초, 기본 0.05)으로 요청 간 최소 간격을 둘 수 있다.

Author: Pom Kim
"""

from __future__ import annotations

import os
import time
from threading import Lock
from typing import Any

from tmdbapis import TMDbAPIs
from tmdbapis.exceptions import NotFound


class TmdbApiClient:
    """TV 검색 래퍼. 한국어 로케일 이름 우선."""

    def __init__(self, api_key: str, *, language: str = "ko-KR") -> None:
        """API 키와 언어를 저장한다. 클라이언트는 지연 초기화.

        Args:
            self: 이 인스턴스.
            api_key: TMDB API 키.
            language: API 언어 코드.

        Returns:
            None.
        """
        self._api_key = api_key
        self._language = language
        self._tmdb: TMDbAPIs | None = None
        self._rate_lock = Lock()
        self._last_request_mono = 0.0
        self._min_interval_s = max(
            0.0,
            float(os.environ.get("ANIVAULT_TMDB_MIN_INTERVAL", "0.05")),
        )

    def _api(self) -> TMDbAPIs:
        """TMDbAPIs 인스턴스를 최초 호출 시 생성한다.

        Args:
            self: 이 인스턴스.

        Returns:
            초기화된 TMDbAPIs.
        """
        if self._tmdb is None:
            self._tmdb = TMDbAPIs(apikey=self._api_key, language=self._language)
        return self._tmdb

    def search_tv_raw(
        self, query: str, *, first_air_date_year: int | None, max_results: int
    ) -> list[Any]:
        """TV 검색 첫 페이지에서 최대 max_results개의 TVShow 객체를 반환한다.

        Args:
            self: 이 클라이언트.
            query: 검색어.
            first_air_date_year: 첫 방영 연도 필터. None이면 무시.
            max_results: 가져올 최대 개수.

        Returns:
            tmdbapis TVShow 객체 리스트. 없으면 빈 리스트.

        Note:
            스레드 안전한 요청 간 최소 간격은 ``ANIVAULT_TMDB_MIN_INTERVAL``로 조정한다.
        """
        q = (query or "").strip()
        if not q:
            return []
        if self._min_interval_s > 0:
            with self._rate_lock:
                now = time.monotonic()
                wait = self._min_interval_s - (now - self._last_request_mono)
                if wait > 0:
                    time.sleep(wait)
                self._last_request_mono = time.monotonic()
        try:
            pagination = self._api().tv_search(q, first_air_date_year=first_air_date_year)
        except NotFound:
            return []
        return list(pagination.get_results(amount=max_results))
