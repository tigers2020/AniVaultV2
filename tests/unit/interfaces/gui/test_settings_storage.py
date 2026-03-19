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
