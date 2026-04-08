"""tmdb_search_tv_library_port.py

영구 보관용 /search/tv 결과 행 저장소.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.application.dto.search_tv_library import SearchTvLibraryRecord


@runtime_checkable
class TmdbSearchTvLibraryRepository(Protocol):
    """픽스처 정렬 search_tv `results[]` 한 건씩 upsert/get."""

    def upsert(self, record: SearchTvLibraryRecord) -> None:
        """행을 넣거나 갱신한다.

        Args:
            self: 저장소.
            record: 라이브러리 행.

        Returns:
            None.
        """
        ...

    def get(self, tmdb_id: int, language: str) -> SearchTvLibraryRecord | None:
        """단일 행을 조회한다.

        Args:
            self: 저장소.
            tmdb_id: TMDB TV id.
            language: API 언어 코드.

        Returns:
            없으면 None.
        """
        ...
