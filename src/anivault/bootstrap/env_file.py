"""env_file.py

Read and write the TMDB API key from a local `.env` file.

Author: Pom Kim
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv, set_key, unset_key

from anivault.constants.bootstrap import DEFAULT_DOTENV_FILENAME, DOTENV_PATH_ENV, TMDB_API_KEY_ENV

TMDB_API_KEY = TMDB_API_KEY_ENV


def resolve_dotenv_path() -> Path:
    """Resolve the dotenv path for this installation."""
    override = os.environ.get(DOTENV_PATH_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / DEFAULT_DOTENV_FILENAME).resolve()


def load_into_os_environ() -> None:
    """Load dotenv values into `os.environ` without overriding existing vars."""
    load_dotenv(resolve_dotenv_path(), override=False)


def read_tmdb_api_key() -> str:
    """Read the TMDB API key from the dotenv file."""
    path = resolve_dotenv_path()
    if not path.is_file():
        return ""
    raw = dotenv_values(path).get(TMDB_API_KEY_ENV)
    if raw is None:
        return ""
    return str(raw).strip()


def write_tmdb_api_key(value: str) -> None:
    """Write or remove the TMDB API key in the dotenv file."""
    path = resolve_dotenv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    key_path = str(path)
    stripped = value.strip()
    if not stripped:
        unset_key(key_path, TMDB_API_KEY_ENV)
        os.environ.pop(TMDB_API_KEY_ENV, None)
        return
    set_key(key_path, TMDB_API_KEY_ENV, stripped)
    os.environ[TMDB_API_KEY_ENV] = stripped
