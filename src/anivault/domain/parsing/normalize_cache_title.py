"""normalize_cache_title.py

parse_cache.parsed_title_normalized용 정규화. 저장소가 아닌 파이프라인/도메인에서 호출.

Author: Pom Kim
"""

from __future__ import annotations


def normalize_title_for_parse_cache(title: str) -> str | None:
    """캐시 인덱스·조회용 정규화 제목을 만든다.

    Args:
        title: 파싱 최종 제목.

    Returns:
        공백 제거 후 casefold. 빈 문자열이면 None.
    """
    t = (title or "").strip()
    if not t:
        return None
    return t.casefold()
