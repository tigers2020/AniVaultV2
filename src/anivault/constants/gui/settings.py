"""Canonical GUI settings schema and defaults."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

CONFIG_DIR: Final[Path] = Path.home() / ".anivault"
CONFIG_FILE: Final[Path] = CONFIG_DIR / "config.json"
DEFAULT_THEME_NAME: Final[str] = "dark"
DEFAULT_UI_LANGUAGE: Final[str] = "ko"
ALLOWED_UI_LANGUAGES: Final[frozenset[str]] = frozenset({"ko", "en"})

PARSE_TMDB_SECRET_KEYS: Final[frozenset[str]] = frozenset({"tmdb_api_key"})
PATH_RULES_KEYS: Final[tuple[str, ...]] = (
    "target_root",
    "path_template",
    "unknown_resolution",
    "unknown_group_folder",
)
PARSE_TMDB_KEYS: Final[tuple[str, ...]] = (
    "ignore_tokens",
    "season_folder_format",
)
SCAN_BUILD_KEYS: Final[tuple[str, ...]] = ("source_path",)
SCAN_BUILD_BOOL_KEYS: Final[frozenset[str]] = frozenset({"auto_scan_on_first_show"})
PIPELINE_RESULTS_KEYS: Final[tuple[str, ...]] = (
    "view_key",
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
    "season_folder_format": "Season{season:02}",
}
DEFAULT_SCAN_BUILD: Final[dict[str, object]] = {
    "source_path": "",
    "auto_scan_on_first_show": True,
}
DEFAULT_PIPELINE_RESULTS: Final[dict[str, object]] = {
    "view_key": "details",
    "selected_index": -1,
}


def default_path_rules() -> dict[str, object]:
    """Return a writable copy of default path rules."""
    return dict(DEFAULT_PATH_RULES)


def default_parse_tmdb() -> dict[str, object]:
    """Return a writable copy of default parse/TMDB settings."""
    return dict(DEFAULT_PARSE_TMDB)


def default_scan_build() -> dict[str, object]:
    """Return a writable copy of default scan/build settings."""
    return dict(DEFAULT_SCAN_BUILD)


def default_pipeline_results() -> dict[str, object]:
    """Return a writable copy of default pipeline UI state."""
    return dict(DEFAULT_PIPELINE_RESULTS)


def default_ui_state() -> dict[str, object]:
    """Return the default UI state payload."""
    return {"pipeline_results": default_pipeline_results()}


def normalize_ui_language(value: object) -> str:
    """Return ko or en; unknown or empty values become DEFAULT_UI_LANGUAGE."""
    if value is None:
        return DEFAULT_UI_LANGUAGE
    s = str(value).strip()
    return s if s in ALLOWED_UI_LANGUAGES else DEFAULT_UI_LANGUAGE


def default_settings_payload(*, include_theme: bool) -> dict[str, Any]:
    """Return the canonical default settings payload."""
    payload: dict[str, Any] = {
        "path_rules": default_path_rules(),
        "parse_tmdb": default_parse_tmdb(),
        "scan_build": default_scan_build(),
        "ui_state": default_ui_state(),
    }
    if include_theme:
        payload["theme"] = DEFAULT_THEME_NAME
        payload["language"] = DEFAULT_UI_LANGUAGE
    return payload


def _merged_string_group(
    data: Mapping[str, Any], *, key: str, defaults: dict[str, object], keys: tuple[str, ...]
) -> dict[str, object]:
    """Return defaults merged with string-compatible values from loaded settings."""
    merged = dict(defaults)
    raw_group = data.get(key)
    if not isinstance(raw_group, Mapping):
        return merged
    for item_key in keys:
        if item_key in raw_group:
            merged[item_key] = str(raw_group[item_key])
    return merged


def path_rules_from_loaded(data: Mapping[str, Any]) -> dict[str, object]:
    """Return loaded path rules merged onto canonical defaults."""
    return _merged_string_group(
        data,
        key="path_rules",
        defaults=DEFAULT_PATH_RULES,
        keys=PATH_RULES_KEYS,
    )


def parse_tmdb_from_loaded(data: Mapping[str, Any]) -> dict[str, object]:
    """Return loaded parse/TMDB settings merged onto canonical defaults."""
    return _merged_string_group(
        data,
        key="parse_tmdb",
        defaults=DEFAULT_PARSE_TMDB,
        keys=PARSE_TMDB_KEYS,
    )


def scan_build_from_loaded(data: Mapping[str, Any]) -> dict[str, object]:
    """Return loaded scan/build settings merged onto canonical defaults."""
    merged = _merged_string_group(
        data,
        key="scan_build",
        defaults=DEFAULT_SCAN_BUILD,
        keys=tuple(key for key in SCAN_BUILD_KEYS if key not in SCAN_BUILD_BOOL_KEYS),
    )
    raw_group = data.get("scan_build")
    if isinstance(raw_group, Mapping):
        for item_key in SCAN_BUILD_BOOL_KEYS:
            raw_value = raw_group.get(item_key)
            if isinstance(raw_value, bool):
                merged[item_key] = raw_value
    return merged


def pipeline_results_from_loaded(data: Mapping[str, Any]) -> dict[str, object]:
    """Return loaded pipeline UI state merged onto canonical defaults."""
    merged = dict(DEFAULT_PIPELINE_RESULTS)
    raw_ui_state = data.get("ui_state")
    if not isinstance(raw_ui_state, Mapping):
        return merged
    raw_pipeline = raw_ui_state.get("pipeline_results")
    if not isinstance(raw_pipeline, Mapping):
        return merged

    view_key = raw_pipeline.get("view_key")
    if isinstance(view_key, str):
        merged["view_key"] = view_key

    selected_index = raw_pipeline.get("selected_index")
    if isinstance(selected_index, int):
        merged["selected_index"] = selected_index
    return merged


def scan_source_path_from_loaded(data: Mapping[str, Any]) -> str:
    """Return the configured scan source path from loaded settings."""
    return str(scan_build_from_loaded(data)["source_path"])


def auto_scan_on_first_show_from_loaded(data: Mapping[str, Any]) -> bool:
    """Return whether organizer auto-scan is enabled."""
    raw_group = data.get("scan_build")
    raw_value: object
    if isinstance(raw_group, Mapping) and "auto_scan_on_first_show" in raw_group:
        raw_value = raw_group["auto_scan_on_first_show"]
    else:
        raw_value = scan_build_from_loaded(data)["auto_scan_on_first_show"]
    if isinstance(raw_value, bool):
        return raw_value
    return str(raw_value).strip().lower() in {"1", "true", "yes"}


def target_root_from_loaded(data: Mapping[str, Any]) -> str:
    """Return the configured target root from loaded settings."""
    return str(path_rules_from_loaded(data)["target_root"])


def parse_ignore_tokens_from_loaded(data: Mapping[str, Any]) -> str:
    """Return the configured ignore-tokens value from loaded settings."""
    return str(parse_tmdb_from_loaded(data)["ignore_tokens"])
