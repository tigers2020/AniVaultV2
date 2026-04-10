"""tmdb_image_url.py

TMDB 이미지 상대 경로 → 공개 CDN URL.

Author: Pom Kim
"""

from __future__ import annotations

from urllib.parse import urlparse

from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path

_TMDB_IMAGE_HOST = "image.tmdb.org"


def _safe_tmdb_cdn_absolute_url(url: str) -> str:
    """허용된 TMDB 이미지 CDN 절대 URL만 https로 반환한다.

    그 외 호스트는 빈 문자열(로드 생략).
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return ""
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return ""
    netloc = (parsed.netloc or "").lower()
    if "@" in netloc:
        return ""
    host = netloc.split(":", 1)[0]
    if host != _TMDB_IMAGE_HOST:
        return ""
    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    frag = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"https://{_TMDB_IMAGE_HOST}{path}{query}{frag}"


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
    if p.startswith("//"):
        p = "https:" + p
    if p.startswith("http"):
        return _safe_tmdb_cdn_absolute_url(p)
    return f"https://{_TMDB_IMAGE_HOST}/t/p/{size}{p}"


def tmdb_backdrop_cdn_url(backdrop_path: str | None, *, size: str = "w780") -> str:
    """backdrop_path를 백드롭용 CDN URL로 만든다.

    Args:
        backdrop_path: API `backdrop_path` 또는 이미 절대 URL.
        size: TMDB `t/p/{size}` 세그먼트.

    Returns:
        https URL. 비어 있으면 "".
    """
    p = normalize_tmdb_remote_image_path(backdrop_path)
    if not p:
        return ""
    if p.startswith("//"):
        p = "https:" + p
    if p.startswith("http"):
        return _safe_tmdb_cdn_absolute_url(p)
    return f"https://{_TMDB_IMAGE_HOST}/t/p/{size}{p}"
