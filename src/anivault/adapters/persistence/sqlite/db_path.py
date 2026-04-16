"""db_path.py

AniVault SQLite DB·포스터 캐시·operation 로그 경로.

모든 경로는 APP_STATE_DIR(~/.anivault)에서 파생한다.

Author: Pom Kim
"""

from pathlib import Path

from anivault.constants.paths import APP_STATE_DIR


def default_anivault_db_path() -> Path:
    """기본 AniVault DB 경로를 반환한다.

    Returns:
        `~/.anivault/anivault.db`.
    """
    return APP_STATE_DIR / "anivault.db"


def ensure_db_parent_dir(db_path: Path) -> None:
    """DB 파일의 부모 디렉터리가 없으면 만든다.

    Args:
        db_path: SQLite 파일 절대 경로.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)


def default_poster_cache_dir() -> Path:
    """TMDB 포스터·백드롭 로컬 캐시 디렉터리를 반환한다.

    Returns:
        `~/.anivault/posters`.
    """
    return APP_STATE_DIR / "posters"


def ensure_poster_cache_dir() -> Path:
    """포스터 캐시 디렉터리가 없으면 만들고 절대 경로를 반환한다.

    Returns:
        `default_poster_cache_dir()`의 resolve 결과.
    """
    d = default_poster_cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_operation_logs_dir() -> Path:
    """정리(apply) operation 로그 디렉터리를 반환한다.

    Returns:
        `~/.anivault/logs`.
    """
    return APP_STATE_DIR / "logs"
