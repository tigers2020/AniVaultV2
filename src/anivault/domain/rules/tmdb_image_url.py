"""tmdb_image_url.py

TMDB 이미지 상대 경로 → 공개 CDN URL.

Author: Pom Kim
"""

from __future__ import annotations

from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path


def tmdb_poster_cdn_url(poster_path: str | None, *, size: str = "w342") -> str:
    """poster_path를 포스터용 CDN URL로 만든다.

    Args:
        poster_path: API 상대 경로 또는 이미 절대 URL.
        size: TMDB `t/p/{size}` 세그먼트.

    Returns:
        https URL. 비어 있으면 "".
    """
    p = normalize_tmdb_remote_image_path(poster_path)
    if not p:
        return ""
    if p.startswith("http"):
        return p
    return f"https://image.tmdb.org/t/p/{size}{p}"


def tmdb_backdrop_cdn_url(backdrop_path: str | None, *, size: str = "w780") -> str:
    """backdrop_path를 백드롭용 CDN URL로 만든다.

    Args:
        backdrop_path: API 상대 경로 또는 이미 절대 URL.
        size: TMDB `t/p/{size}` 세그먼트.

    Returns:
        https URL. 비어 있으면 "".
    """
    p = normalize_tmdb_remote_image_path(backdrop_path)
    if not p:
        return ""
    if p.startswith("http"):
        return p
    return f"https://image.tmdb.org/t/p/{size}{p}"
