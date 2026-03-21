"""env_file.py

`.env` 경로 결정 및 TMDB API 키 읽기·쓰기. 비밀은 config.json에 넣지 않는다.

Author: Pom Kim
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv, set_key, unset_key

TMDB_API_KEY = "TMDB_API_KEY"
DOTENV_PATH_ENV = "ANIVAULT_DOTENV_PATH"


def resolve_dotenv_path() -> Path:
    """사용할 `.env` 파일 경로를 반환한다.

    Args:
        없음.

    Returns:
        `ANIVAULT_DOTENV_PATH`가 있으면 그 경로, 없으면 현재 작업 디렉터리의 `.env`.
    """
    override = os.environ.get(DOTENV_PATH_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / ".env").resolve()


def load_into_os_environ() -> None:
    """`.env`를 `os.environ`에 로드한다. 이미 있는 키는 덮어쓰지 않는다.

    Args:
        없음.

    Returns:
        None.
    """
    load_dotenv(resolve_dotenv_path(), override=False)


def read_tmdb_api_key() -> str:
    """`.env` 파일에서 `TMDB_API_KEY` 값을 읽는다.

    Args:
        없음.

    Returns:
        키 문자열. 파일이 없거나 키가 없으면 빈 문자열.
    """
    path = resolve_dotenv_path()
    if not path.is_file():
        return ""
    raw = dotenv_values(path).get(TMDB_API_KEY)
    if raw is None:
        return ""
    return str(raw).strip()


def write_tmdb_api_key(value: str) -> None:
    """`.env`에 `TMDB_API_KEY`를 쓰거나 제거하고 `os.environ`에 반영한다.

    Args:
        value: 저장할 API 키. 공백만이면 키를 제거한다.

    Returns:
        None.
    """
    path = resolve_dotenv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    key_path = str(path)
    stripped = value.strip()
    if not stripped:
        unset_key(key_path, TMDB_API_KEY)
        os.environ.pop(TMDB_API_KEY, None)
        return
    set_key(key_path, TMDB_API_KEY, stripped)
    os.environ[TMDB_API_KEY] = stripped
