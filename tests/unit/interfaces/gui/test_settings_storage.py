"""Tests for GUI settings storage persistence."""

import json
from pathlib import Path

from anivault.constants.gui.settings import (
    DEFAULT_PARSE_TMDB,
    DEFAULT_PATH_RULES,
    DEFAULT_PIPELINE_RESULTS,
    DEFAULT_SCAN_BUILD,
    auto_scan_on_first_show_from_loaded,
    parse_ignore_tokens_from_loaded,
    path_rules_from_loaded,
    pipeline_results_from_loaded,
    scan_build_from_loaded,
    scan_source_path_from_loaded,
    target_root_from_loaded,
)
from anivault.interfaces.gui import settings_storage


def test_load_all_includes_pipeline_result_defaults(tmp_path: Path, monkeypatch) -> None:
    """load_all should include ui_state.pipeline_results defaults."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    loaded = settings_storage.load_all()
    pipeline = loaded["ui_state"]["pipeline_results"]

    assert pipeline["view_key"] == "details"
    assert pipeline["selected_index"] == -1


def test_get_defaults_uses_canonical_settings_schema() -> None:
    """get_defaults should mirror the canonical settings module defaults."""
    defaults = settings_storage.get_defaults()

    assert defaults["path_rules"] == DEFAULT_PATH_RULES
    assert defaults["parse_tmdb"] == DEFAULT_PARSE_TMDB
    assert defaults["scan_build"] == DEFAULT_SCAN_BUILD
    assert "theme" not in defaults


def test_settings_helpers_merge_defaults_for_partial_loaded_payload() -> None:
    """Helper readers should merge partial loaded settings with canonical defaults."""
    loaded = {
        "path_rules": {"target_root": "F:/Library"},
        "parse_tmdb": {"ignore_tokens": "x264"},
        "scan_build": {"source_path": "F:/Anime"},
        "ui_state": {"pipeline_results": {"view_key": "icon_m"}},
    }

    assert path_rules_from_loaded(loaded)["target_root"] == "F:/Library"
    assert (
        path_rules_from_loaded(loaded)["unknown_group_folder"]
        == DEFAULT_PATH_RULES["unknown_group_folder"]
    )
    assert parse_ignore_tokens_from_loaded(loaded) == "x264"
    assert scan_source_path_from_loaded(loaded) == "F:/Anime"
    assert scan_build_from_loaded(loaded)["source_path"] == "F:/Anime"
    assert target_root_from_loaded(loaded) == "F:/Library"
    assert pipeline_results_from_loaded(loaded)["view_key"] == "icon_m"
    assert (
        pipeline_results_from_loaded(loaded)["selected_index"]
        == DEFAULT_PIPELINE_RESULTS["selected_index"]
    )


def test_auto_scan_helper_accepts_bool_and_string_inputs() -> None:
    """Auto-scan helper should preserve legacy truthy string handling."""
    assert auto_scan_on_first_show_from_loaded({"scan_build": {"auto_scan_on_first_show": True}})
    assert auto_scan_on_first_show_from_loaded({"scan_build": {"auto_scan_on_first_show": "yes"}})
    assert not auto_scan_on_first_show_from_loaded(
        {"scan_build": {"auto_scan_on_first_show": "no"}}
    )


def test_save_all_merges_pipeline_result_state(tmp_path: Path, monkeypatch) -> None:
    """save_all should persist ui_state.pipeline_results fields."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    settings_storage.save_all(
        {
            "ui_state": {
                "pipeline_results": {
                    "view_key": "icon_m",
                    "selected_index": 3,
                }
            }
        }
    )
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    pipeline = raw["ui_state"]["pipeline_results"]
    assert pipeline["view_key"] == "icon_m"
    assert pipeline["selected_index"] == 3

    loaded = settings_storage.load_all()
    loaded_pipeline = loaded["ui_state"]["pipeline_results"]
    assert loaded_pipeline["view_key"] == "icon_m"
    assert loaded_pipeline["selected_index"] == 3


def test_load_all_falls_back_for_invalid_pipeline_result_types(tmp_path: Path, monkeypatch) -> None:
    """Invalid ui_state.pipeline_results types should safely fall back."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "ui_state": {
                    "pipeline_results": {
                        "view_key": 123,
                        "selected_index": "bad",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    loaded = settings_storage.load_all()
    pipeline = loaded["ui_state"]["pipeline_results"]
    assert pipeline["view_key"] == "details"
    assert pipeline["selected_index"] == -1


def test_load_all_accepts_selected_index_bool_as_int(tmp_path: Path, monkeypatch) -> None:
    """selected_index historically accepted bool values (bool is an int subclass in Python)."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "ui_state": {
                    "pipeline_results": {
                        "selected_index": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    loaded = settings_storage.load_all()
    pipeline = loaded["ui_state"]["pipeline_results"]
    assert pipeline["selected_index"] == 1


def test_load_all_migrates_scan_build_target_path_to_path_rules_target_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Legacy scan_build.target_path becomes path_rules.target_root when target_root absent."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "scan_build": {
                    "source_path": "D:/In",
                    "target_path": "D:/LegacyTarget",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    loaded = settings_storage.load_all()
    assert loaded["path_rules"]["target_root"] == "D:/LegacyTarget"
    assert "target_path" not in loaded["scan_build"]


def test_load_all_keeps_path_rules_target_root_over_legacy_scan_target(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Explicit path_rules.target_root wins over scan_build.target_path."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        json.dumps(
            {
                "path_rules": {"target_root": "E:/FromPathRules"},
                "scan_build": {"target_path": "E:/FromScanBuild"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    loaded = settings_storage.load_all()
    assert loaded["path_rules"]["target_root"] == "E:/FromPathRules"


def test_save_all_does_not_persist_tmdb_api_key_in_config(tmp_path: Path, monkeypatch) -> None:
    """parse_tmdb must never store tmdb_api_key in config.json (`.env` only)."""
    config_dir = tmp_path / ".anivault"
    config_file = config_dir / "config.json"
    monkeypatch.setattr(settings_storage, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(settings_storage, "CONFIG_FILE", config_file)

    settings_storage.save_all(
        {
            "parse_tmdb": {
                "ignore_tokens": "x",
                "tmdb_api_key": "super-secret",
            },
        }
    )
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    assert "tmdb_api_key" not in raw.get("parse_tmdb", {})
    assert raw["parse_tmdb"]["ignore_tokens"] == "x"
