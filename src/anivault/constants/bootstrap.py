"""Bootstrap and environment constants."""

from __future__ import annotations

from typing import Final

TMDB_API_KEY_ENV: Final[str] = "TMDB_API_KEY"
DOTENV_PATH_ENV: Final[str] = "ANIVAULT_DOTENV_PATH"
SUPPORTED_VIDEO_EXTENSIONS: Final[tuple[str, ...]] = (".mkv", ".mp4", ".avi", ".mov", ".webm")
