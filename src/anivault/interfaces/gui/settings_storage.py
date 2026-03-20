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
SCAN_BUILD_KEYS = ("source_path", "tmdb_mode", "unknown_mode")
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


def _default_result() -> dict[str, Any]:
    """Return default merged config (theme/path_rules/parse_tmdb/scan_build/ui_state)."""
    return {
        "theme": "dark",
        "path_rules": dict(DEFAULT_PATH_RULES),
        "parse_tmdb": dict(DEFAULT_PARSE_TMDB),
        "scan_build": dict(DEFAULT_SCAN_BUILD),
        "ui_state": {
            "pipeline_results": dict(DEFAULT_PIPELINE_RESULTS),
        },
    }


def _safe_load_config_data() -> Any:
    """Safely load config.json, returning raw decoded JSON (or None)."""
    with suppress(OSError, ValueError):
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return None


def _merge_string_key_group(
    *,
    target_group: dict[str, str],
    loaded_data_group: Any,
    keys: tuple[str, ...],
) -> None:
    """Update target_group[key] = str(loaded_data_group[key]) when key exists."""
    if not isinstance(loaded_data_group, dict):
        return
    for key in keys:
        if key in loaded_data_group:
            target_group[key] = str(loaded_data_group[key])


def _migrate_scan_build_target_path_to_target_root(
    result: dict[str, Any],
    data: dict[str, Any],
) -> None:
    """If path_rules.target_root was never stored, adopt legacy scan_build.target_path."""
    path_loaded = data.get("path_rules")
    path_has_root = isinstance(path_loaded, dict) and "target_root" in path_loaded
    if path_has_root:
        return
    scan_loaded = data.get("scan_build")
    if not isinstance(scan_loaded, dict):
        return
    if "target_path" not in scan_loaded:
        return
    cast(dict[str, str], result["path_rules"])["target_root"] = str(scan_loaded["target_path"])


def _merge_loaded_data(result: dict[str, Any], data: dict[str, Any]) -> None:
    """Merge loaded config into the existing result dict in-place."""
    if "theme" in data:
        result["theme"] = str(data["theme"])

    _merge_string_key_group(
        target_group=cast(dict[str, str], result["path_rules"]),
        loaded_data_group=data.get("path_rules"),
        keys=PATH_RULES_KEYS,
    )
    _merge_string_key_group(
        target_group=cast(dict[str, str], result["parse_tmdb"]),
        loaded_data_group=data.get("parse_tmdb"),
        keys=PARSE_TMDB_KEYS,
    )
    _merge_string_key_group(
        target_group=cast(dict[str, str], result["scan_build"]),
        loaded_data_group=data.get("scan_build"),
        keys=SCAN_BUILD_KEYS,
    )

    _migrate_scan_build_target_path_to_target_root(result, data)

    ui_state = data.get("ui_state")
    if not isinstance(ui_state, dict):
        return

    pipeline_results = ui_state.get("pipeline_results")
    if not isinstance(pipeline_results, dict):
        return

    result_pipeline = cast(
        dict[str, Any],
        cast(dict[str, Any], result["ui_state"])["pipeline_results"],
    )

    if "selected_index" in pipeline_results:
        value = pipeline_results["selected_index"]
        if isinstance(value, int):
            result_pipeline["selected_index"] = value

    if "details_pane" in pipeline_results:
        value = pipeline_results["details_pane"]
        if isinstance(value, bool):
            result_pipeline["details_pane"] = value

    if "preview_pane" in pipeline_results:
        value = pipeline_results["preview_pane"]
        if isinstance(value, bool):
            result_pipeline["preview_pane"] = value

    if "view_key" in pipeline_results:
        value = pipeline_results["view_key"]
        if isinstance(value, str):
            result_pipeline["view_key"] = value


def load_all() -> dict[str, Any]:
    """Load full config. Returns merged dict with defaults for missing keys."""
    result = _default_result()
    if not CONFIG_FILE.exists():
        return result

    loaded = _safe_load_config_data()
    if not isinstance(loaded, dict):
        return result

    _merge_loaded_data(result, cast(dict[str, Any], loaded))
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
