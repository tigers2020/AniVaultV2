"""poster_remote_path.py

TMDB 포스터·백드롭 `remote_path`(API 상대 경로) 정규화.

Author: Pom Kim
"""

from __future__ import annotations


def normalize_tmdb_remote_image_path(path: str | None) -> str:
    """TMDB 이미지 상대 경로를 DB·비교용으로 정규화한다.

    Args:
        path: API `poster_path` / `backdrop_path` 또는 None.

    Returns:
        앞뒤 공백 제거 문자열. None은 빈 문자열과 동일.
    """
    if path is None:
        return ""
    return (path or "").strip()
