"""Settings persistence. Load/save to ~/.anivault/config.json."""

import json
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

CONFIG_DIR = Path.home() / ".anivault"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Schema keys for each settings group
PATH_RULES_KEYS = ("target_root", "path_template", "unknown_resolution", "unknown_group_folder")
PARSE_TMDB_KEYS = (
    "ignore_tokens",
    "video_extensions",
    "tmdb_search_mode",
    "season_folder_format",
)
SCAN_BUILD_KEYS = ("source_path", "target_path", "tmdb_mode", "unknown_mode")
PIPELINE_RESULTS_KEYS = ("view_key", "details_pane", "preview_pane", "selected_index")

DEFAULT_PATH_RULES = {
    "target_root": "G:/AniSorted",
    "path_template": r"{target}\{resolution}\{year}\{korean_title_group}\Season{season:02}\{original_filename}",
    "unknown_resolution": "Unknown",
    "unknown_group_folder": "Needs_Review",
}
DEFAULT_PARSE_TMDB = {
    "ignore_tokens": "1080p, 720p, x264, WEBRip, BluRay, AAC, HEVC",
    "video_extensions": ".mkv, .mp4, .avi",
    "tmdb_search_mode": "Prefer TV and Korean localized title",
    "season_folder_format": "Season{season:02}",
}
DEFAULT_SCAN_BUILD = {
    "source_path": "",
    "target_path": "G:/AniSorted",
    "tmdb_mode": "TMDB TV Search",
    "unknown_mode": "Unknown to Needs_Review",
}
DEFAULT_PIPELINE_RESULTS = {
    "view_key": "details",
    "details_pane": False,
    "preview_pane": False,
    "selected_index": -1,
}


def get_defaults() -> dict[str, Any]:
    """Return default settings for path_rules, parse_tmdb, scan_build, ui_state."""
    return {
        "path_rules": dict(DEFAULT_PATH_RULES),
        "parse_tmdb": dict(DEFAULT_PARSE_TMDB),
        "scan_build": dict(DEFAULT_SCAN_BUILD),
        "ui_state": {
            "pipeline_results": dict(DEFAULT_PIPELINE_RESULTS),
        },
    }


def _ensure_dir() -> None:
    with suppress(OSError):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_all() -> dict[str, Any]:
    """Load full config. Returns merged dict with defaults for missing keys."""
    result: dict[str, Any] = {
        "theme": "dark",
        "path_rules": dict(DEFAULT_PATH_RULES),
        "parse_tmdb": dict(DEFAULT_PARSE_TMDB),
        "scan_build": dict(DEFAULT_SCAN_BUILD),
        "ui_state": {
            "pipeline_results": dict(DEFAULT_PIPELINE_RESULTS),
        },
    }
    if not CONFIG_FILE.exists():
        return result
    with suppress(OSError, ValueError):
        loaded: Any = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            return result
        data = loaded
        if "theme" in data:
            result["theme"] = str(data["theme"])
        for key in PATH_RULES_KEYS:
            if "path_rules" in data and key in data["path_rules"]:
                cast(dict[str, str], result["path_rules"])[key] = str(data["path_rules"][key])
        for key in PARSE_TMDB_KEYS:
            if "parse_tmdb" in data and key in data["parse_tmdb"]:
                cast(dict[str, str], result["parse_tmdb"])[key] = str(data["parse_tmdb"][key])
        for key in SCAN_BUILD_KEYS:
            if "scan_build" in data and key in data["scan_build"]:
                cast(dict[str, str], result["scan_build"])[key] = str(data["scan_build"][key])
        ui_state = data.get("ui_state")
        if isinstance(ui_state, dict):
            pipeline_results = ui_state.get("pipeline_results")
            if isinstance(pipeline_results, dict):
                result_pipeline = cast(
                    dict[str, Any],
                    cast(dict[str, Any], result["ui_state"])["pipeline_results"],
                )
                for key in PIPELINE_RESULTS_KEYS:
                    if key in pipeline_results:
                        value = pipeline_results[key]
                        if key == "selected_index":
                            if isinstance(value, int):
                                result_pipeline[key] = value
                        elif key in ("details_pane", "preview_pane"):
                            if isinstance(value, bool):
                                result_pipeline[key] = value
                        elif key == "view_key" and isinstance(value, str):
                            result_pipeline[key] = value
    return result


def save_all(data: dict[str, Any]) -> None:
    """Save config. Merges with existing file to preserve theme and other keys."""
    _ensure_dir()
    existing: dict[str, Any] = {}
    if CONFIG_FILE.exists():
        with suppress(OSError, ValueError):
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
    for key, val in data.items():
        if isinstance(val, dict):
            existing.setdefault(key, {})
            if isinstance(existing[key], dict):
                existing[key].update(val)
        else:
            existing[key] = val
    with suppress(OSError):
        CONFIG_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
