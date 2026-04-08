"""Bootstrap and environment constants."""

from __future__ import annotations

from pathlib import Path
from typing import Final

TMDB_API_KEY_ENV: Final[str] = "TMDB_API_KEY"
DOTENV_PATH_ENV: Final[str] = "ANIVAULT_DOTENV_PATH"
DEFAULT_DOTENV_FILENAME: Final[str] = ".env"

DEFAULT_LOGS_DIR: Final[Path] = Path(".anivault/logs")
SUPPORTED_VIDEO_EXTENSIONS: Final[tuple[str, ...]] = (".mkv", ".mp4", ".avi", ".mov", ".webm")
