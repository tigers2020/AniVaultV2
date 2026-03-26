"""poster_cache_filename.py

로컬 포스터 캐시 파일 경로(해시 기반 파일명).

Author: Pom Kim
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path


def short_hash_remote_path(remote_path: str) -> str:
    """remote_path에서 짧은 16진 해시 접두를 만든다.

    Args:
        remote_path: 정규화 전·후 TMDB 상대 경로.

    Returns:
        SHA-256 앞 8자(소문자 hex).
    """
    norm = normalize_tmdb_remote_image_path(remote_path)
    if not norm:
        return "00000000"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:8]


def poster_cache_file_path(
    cache_dir: Path,
    tmdb_id: int,
    image_kind: str,
    remote_path: str,
    *,
    extension: str = ".jpg",
) -> Path:
    """캐시 디렉터리 아래 로컬 파일 절대 경로를 만든다.

    파일명: `tmdb_{tmdb_id}_{image_kind}_{short_hash}{ext}`

    Args:
        cache_dir: 루트 캐시 디렉터리.
        tmdb_id: TMDB TV 시리즈 id.
        image_kind: poster 또는 backdrop.
        remote_path: TMDB 상대 경로.
        extension: 파일 확장자(기본 .jpg).

    Returns:
        절대 `Path`.
    """
    h = short_hash_remote_path(remote_path)
    name = f"tmdb_{int(tmdb_id)}_{image_kind}_{h}{extension}"
    return cache_dir / name
