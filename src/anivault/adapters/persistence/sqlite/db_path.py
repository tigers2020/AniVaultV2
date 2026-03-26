"""db_path.py

전역 SQLite DB 파일 경로(MVP 단일 파일). implementation_policy §1.

Author: Pom Kim
"""

from pathlib import Path


def default_anivault_db_path() -> Path:
    """기본 AniVault DB 경로를 반환한다.

    Args:
        없음.

    Returns:
        `~/.anivault/anivault.db`.
    """
    return Path.home() / ".anivault" / "anivault.db"


def ensure_db_parent_dir(db_path: Path) -> None:
    """DB 파일의 부모 디렉터리가 없으면 만든다.

    Args:
        db_path: SQLite 파일 절대 경로.

    Returns:
        None.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)


def default_poster_cache_dir() -> Path:
    """TMDB 포스터·백드롭 로컬 캐시 디렉터리를 반환한다.

    Args:
        없음.

    Returns:
        `~/.anivault/posters`.
    """
    return Path.home() / ".anivault" / "posters"


def ensure_poster_cache_dir() -> Path:
    """포스터 캐시 디렉터리가 없으면 만들고 절대 경로를 반환한다.

    Args:
        없음.

    Returns:
        `default_poster_cache_dir()`의 resolve 결과.
    """
    d = default_poster_cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d
