"""`.env` path resolution and TMDB API key read/write. Secrets stay out of config.json."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv, set_key, unset_key

TMDB_API_KEY = "TMDB_API_KEY"
DOTENV_PATH_ENV = "ANIVAULT_DOTENV_PATH"


def resolve_dotenv_path() -> Path:
    """Return path to `.env`: `ANIVAULT_DOTENV_PATH` or else `cwd/.env`."""
    override = os.environ.get(DOTENV_PATH_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return (Path.cwd() / ".env").resolve()


def load_into_os_environ() -> None:
    """Load `.env` into `os.environ` without overriding existing variables."""
    load_dotenv(resolve_dotenv_path(), override=False)


def read_tmdb_api_key() -> str:
    """Read `TMDB_API_KEY` from the `.env` file (not only from `os.environ`)."""
    path = resolve_dotenv_path()
    if not path.is_file():
        return ""
    raw = dotenv_values(path).get(TMDB_API_KEY)
    if raw is None:
        return ""
    return str(raw).strip()


def write_tmdb_api_key(value: str) -> None:
    """Write or remove `TMDB_API_KEY` in `.env` and mirror it in `os.environ`."""
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
