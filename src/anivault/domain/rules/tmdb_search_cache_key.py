"""tmdb_search_cache_key.py

TMDB 검색 캐시 키 생성. 언어·정규화 쿼리·연도·페이지를 안정적으로 직렬화한다.

Author: Pom Kim
"""

from __future__ import annotations

from anivault.domain.rules.tmdb_search_query import normalize_tmdb_search_query


def build_tmdb_search_cache_key(
    language: str,
    query: str,
    *,
    year: int | None,
    page: int = 1,
) -> str:
    """검색 캐시 행 `cache_key` 문자열을 만든다.

    형식: `tmdb_search:{language}:{normalized_query}:{token_year}:{page}`

    Args:
        language: API 언어 코드(예: ko-KR).
        query: 원본 검색어(`normalize_tmdb_search_query` 적용 전).
        year: 연도 필터. None이면 `none` 토큰.
        page: TMDB 페이지(현재 클라이언트는 1 고정).

    Returns:
        고유 캐시 키.
    """
    lang = (language or "").strip() or "und"
    nq = normalize_tmdb_search_query(query)
    yt = "none" if year is None else str(int(year))
    pg = max(1, int(page))
    return f"tmdb_search:{lang}:{nq}:{yt}:{pg}"
