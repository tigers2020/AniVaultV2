"""persist_search_tv_library.py

/search/tv 결과 행을 영구 라이브러리 테이블에 기록한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from anivault.application.ports.tmdb_search_tv_library_port import TmdbSearchTvLibraryRepository
from anivault.contracts.tmdb import SearchTvLibraryRecord


def make_execute(
    repo: TmdbSearchTvLibraryRepository,
) -> Callable[[Sequence[SearchTvLibraryRecord]], None]:
    """저장소를 주입해 실행 함수를 만든다."""

    def execute(records: Sequence[SearchTvLibraryRecord]) -> None:
        for r in records:
            if r.tmdb_id <= 0:
                continue
            repo.upsert(r)

    return execute
