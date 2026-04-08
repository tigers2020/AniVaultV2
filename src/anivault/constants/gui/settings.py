"""GUI settings storage constants."""

from __future__ import annotations

from pathlib import Path
from typing import Final

CONFIG_DIR: Final[Path] = Path.home() / ".anivault"
CONFIG_FILE: Final[Path] = CONFIG_DIR / "config.json"
DEFAULT_THEME_NAME: Final[str] = "dark"

PARSE_TMDB_SECRET_KEYS: Final[frozenset[str]] = frozenset({"tmdb_api_key"})
PATH_RULES_KEYS: Final[tuple[str, ...]] = (
    "target_root",
    "path_template",
    "unknown_resolution",
    "unknown_group_folder",
)
PARSE_TMDB_KEYS: Final[tuple[str, ...]] = (
    "ignore_tokens",
    "video_extensions",
    "tmdb_search_mode",
    "season_folder_format",
)
SCAN_BUILD_KEYS: Final[tuple[str, ...]] = ("source_path", "tmdb_mode", "unknown_mode")
SCAN_BUILD_BOOL_KEYS: Final[frozenset[str]] = frozenset({"auto_scan_on_first_show"})
PIPELINE_RESULTS_KEYS: Final[tuple[str, ...]] = (
    "view_key",
    "details_pane",
    "preview_pane",
    "selected_index",
)

DEFAULT_PATH_RULES: Final[dict[str, object]] = {
    "target_root": "G:/AniSorted",
    "path_template": r"{target}\{resolution}\{year}\{korean_title_group}\Season{season:02}\{original_filename}",
    "unknown_resolution": "Unknown",
    "unknown_group_folder": "Needs_Review",
}
DEFAULT_PARSE_TMDB: Final[dict[str, object]] = {
    "ignore_tokens": "1080p, 720p, x264, WEBRip, BluRay, AAC, HEVC",
    "video_extensions": ".mkv, .mp4, .avi",
    "tmdb_search_mode": "Prefer TV and Korean localized title",
    "season_folder_format": "Season{season:02}",
}
DEFAULT_SCAN_BUILD: Final[dict[str, object]] = {
    "source_path": "",
    "tmdb_mode": "TMDB TV Search",
    "unknown_mode": "Unknown to Needs_Review",
    "auto_scan_on_first_show": True,
}
DEFAULT_PIPELINE_RESULTS: Final[dict[str, object]] = {
    "view_key": "details",
    "details_pane": False,
    "preview_pane": False,
    "selected_index": -1,
}
