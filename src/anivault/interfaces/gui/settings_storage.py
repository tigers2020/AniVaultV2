"""settings_storage.py

~/.anivault/config.json 로드·저장. API 키는 config에 넣지 않는다.

Author: Pom Kim
"""

import json
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

CONFIG_DIR = Path.home() / ".anivault"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Never persist in config.json (stored in `.env` only).
PARSE_TMDB_SECRET_KEYS = frozenset({"tmdb_api_key"})

# Schema keys for each settings group
PATH_RULES_KEYS = ("target_root", "path_template", "unknown_resolution", "unknown_group_folder")
PARSE_TMDB_KEYS = (
    "ignore_tokens",
    "video_extensions",
    "tmdb_search_mode",
    "season_folder_format",
)
SCAN_BUILD_KEYS = ("source_path", "tmdb_mode", "unknown_mode")
PIPELINE_RESULTS_KEYS = ("view_key", "details_pane", "selected_index")

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
    "selected_index": -1,
}


def get_defaults() -> dict[str, Any]:
    """path_rules·parse_tmdb·scan_build·ui_state 기본 dict를 반환한다.

    Args:
        없음.

    Returns:
        기본 설정 딕셔너리.
    """
    return {
        "path_rules": dict(DEFAULT_PATH_RULES),
        "parse_tmdb": dict(DEFAULT_PARSE_TMDB),
        "scan_build": dict(DEFAULT_SCAN_BUILD),
        "ui_state": {
            "pipeline_results": dict(DEFAULT_PIPELINE_RESULTS),
        },
    }


def _ensure_dir() -> None:
    """설정 디렉터리를 만든다.

    Args:
        없음.

    Returns:
        None.
    """
    with suppress(OSError):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _default_result() -> dict[str, Any]:
    """theme·각 그룹이 채워진 병합 기본 설정을 반환한다.

    Args:
        없음.

    Returns:
        기본 전체 설정.
    """
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
    """config.json을 읽어 JSON으로 파싱한다.

    Args:
        없음.

    Returns:
        dict 등 파싱 결과 또는 실패 시 None.
    """
    with suppress(OSError, ValueError):
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return None


def _merge_string_key_group(
    *,
    target_group: dict[str, str],
    loaded_data_group: Any,
    keys: tuple[str, ...],
) -> None:
    """로드된 dict에서 지정 키만 str로 target_group에 덮어쓴다.

    Args:
        target_group: 갱신할 대상.
        loaded_data_group: 파일에서 온 하위 dict.
        keys: 허용 키 튜플.

    Returns:
        None.
    """
    if not isinstance(loaded_data_group, dict):
        return
    for key in keys:
        if key in loaded_data_group:
            target_group[key] = str(loaded_data_group[key])


def _migrate_scan_build_target_path_to_target_root(
    result: dict[str, Any],
    data: dict[str, Any],
) -> None:
    """구버전 scan_build.target_path를 path_rules.target_root로 승격한다.

    Args:
        result: 병합 중 결과 dict.
        data: 파일에서 읽은 원본.

    Returns:
        None.
    """
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
    """로드된 dict를 result에 제자리 병합한다.

    Args:
        result: 기본에서 시작한 결과.
        data: 파일 내용.

    Returns:
        None.
    """
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

    if "view_key" in pipeline_results:
        value = pipeline_results["view_key"]
        if isinstance(value, str):
            result_pipeline["view_key"] = value


def load_all() -> dict[str, Any]:
    """전체 설정을 읽어 기본값과 병합한다.

    Args:
        없음.

    Returns:
        병합된 설정 dict.
    """
    result = _default_result()
    if not CONFIG_FILE.exists():
        return result

    loaded = _safe_load_config_data()
    if not isinstance(loaded, dict):
        return result

    _merge_loaded_data(result, cast(dict[str, Any], loaded))
    return result


def save_all(data: dict[str, Any]) -> None:
    """부분 dict를 기존 파일과 병합해 저장한다.

    Args:
        data: 갱신할 키·하위 dict.

    Returns:
        None.
    """
    _ensure_dir()
    to_merge = dict(data)
    parse_tmdb = to_merge.get("parse_tmdb")
    if isinstance(parse_tmdb, dict):
        to_merge["parse_tmdb"] = {
            k: v for k, v in parse_tmdb.items() if k not in PARSE_TMDB_SECRET_KEYS
        }
    existing: dict[str, Any] = {}
    if CONFIG_FILE.exists():
        with suppress(OSError, ValueError):
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
    for key, val in to_merge.items():
        if isinstance(val, dict):
            existing.setdefault(key, {})
            if isinstance(existing[key], dict):
                existing[key].update(val)
        else:
            existing[key] = val
    with suppress(OSError):
        CONFIG_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
