"""settings_storage.py

~/.anivault/config.json 로드·저장. API 키는 config에 넣지 않는다.

Author: Pom Kim
"""

import json
from contextlib import suppress
from typing import Any

from anivault.constants.gui.settings import (
    CONFIG_DIR,
    CONFIG_FILE,
    PARSE_TMDB_KEYS,
    PARSE_TMDB_SECRET_KEYS,
    PATH_RULES_KEYS,
    SCAN_BUILD_BOOL_KEYS,
    SCAN_BUILD_KEYS,
    default_settings_payload,
    normalize_ui_language,
)


def get_defaults() -> dict[str, Any]:
    """path_rules·parse_tmdb·scan_build·ui_state 기본 dict를 반환한다.

    Args:
        없음.

    Returns:
        기본 설정 딕셔너리.
    """
    return default_settings_payload(include_theme=False)


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
    return default_settings_payload(include_theme=True)


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


def _string_key_dict(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): item for key, item in value.items()}


def _result_group(result: dict[str, Any], key: str) -> dict[str, Any]:
    group = _string_key_dict(result.get(key))
    if group is None:
        group = {}
    result[key] = group
    return group


def _merge_string_key_group(
    *,
    target_group: dict[str, Any],
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
    _result_group(result, "path_rules")["target_root"] = str(scan_loaded["target_path"])


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
    if "language" in data:
        result["language"] = normalize_ui_language(data["language"])

    _merge_string_key_group(
        target_group=_result_group(result, "path_rules"),
        loaded_data_group=data.get("path_rules"),
        keys=PATH_RULES_KEYS,
    )
    _merge_string_key_group(
        target_group=_result_group(result, "parse_tmdb"),
        loaded_data_group=data.get("parse_tmdb"),
        keys=PARSE_TMDB_KEYS,
    )
    scan_loaded = data.get("scan_build")
    str_keys = tuple(k for k in SCAN_BUILD_KEYS if k not in SCAN_BUILD_BOOL_KEYS)
    _merge_string_key_group(
        target_group=_result_group(result, "scan_build"),
        loaded_data_group=scan_loaded,
        keys=str_keys,
    )
    _merge_scan_build_bool_keys(result, scan_loaded)

    _migrate_scan_build_target_path_to_target_root(result, data)

    ui_state = data.get("ui_state")
    if not isinstance(ui_state, dict):
        return

    pipeline_results = ui_state.get("pipeline_results")
    if not isinstance(pipeline_results, dict):
        return

    result_pipeline = _result_group(_result_group(result, "ui_state"), "pipeline_results")
    _merge_pipeline_results(result_pipeline, pipeline_results)


def _merge_scan_build_bool_keys(result: dict[str, Any], scan_loaded: Any) -> None:
    """scan_build의 bool 키를 안전하게 병합한다."""
    if not isinstance(scan_loaded, dict):
        return
    scan_target = _result_group(result, "scan_build")
    for key in SCAN_BUILD_BOOL_KEYS:
        value = scan_loaded.get(key)
        if isinstance(value, bool):
            scan_target[key] = value


def _merge_pipeline_results(
    result_pipeline: dict[str, Any], pipeline_results: dict[str, Any]
) -> None:
    """pipeline_results 하위 값들을 타입 검증 후 병합한다."""
    typed_assignments: tuple[tuple[str, type[Any]], ...] = (
        ("selected_index", int),
        ("view_key", str),
    )
    for key, expected_type in typed_assignments:
        value = pipeline_results.get(key)
        if isinstance(value, expected_type):
            result_pipeline[key] = value


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

    loaded = _string_key_dict(_safe_load_config_data())
    if loaded is None:
        return result

    _merge_loaded_data(result, loaded)
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
    if "language" in to_merge:
        to_merge["language"] = normalize_ui_language(to_merge["language"])
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
            current = existing.get(key)
            if isinstance(current, dict):
                current.update(val)
            else:
                existing[key] = dict(val)
        else:
            existing[key] = val
    with suppress(OSError):
        CONFIG_FILE.write_text(json.dumps(existing, indent=2), encoding="utf-8")
