"""Tests for GUI settings storage persistence."""

import json
from pathlib import Path

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
    assert pipeline["details_pane"] is False
    assert pipeline["preview_pane"] is False
    assert pipeline["selected_index"] == -1


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
                    "details_pane": True,
                    "preview_pane": False,
                    "selected_index": 3,
                }
            }
        }
    )
    raw = json.loads(config_file.read_text(encoding="utf-8"))
    pipeline = raw["ui_state"]["pipeline_results"]
    assert pipeline["view_key"] == "icon_m"
    assert pipeline["details_pane"] is True
    assert pipeline["preview_pane"] is False
    assert pipeline["selected_index"] == 3

    loaded = settings_storage.load_all()
    loaded_pipeline = loaded["ui_state"]["pipeline_results"]
    assert loaded_pipeline["view_key"] == "icon_m"
    assert loaded_pipeline["details_pane"] is True
    assert loaded_pipeline["preview_pane"] is False
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
                        "details_pane": "yes",
                        "preview_pane": "no",
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
    assert pipeline["details_pane"] is False
    assert pipeline["preview_pane"] is False
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
                    "tmdb_mode": "TMDB TV Search",
                    "unknown_mode": "Unknown to Needs_Review",
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
