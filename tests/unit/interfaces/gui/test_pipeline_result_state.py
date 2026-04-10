from __future__ import annotations

from anivault.interfaces.gui.templates import pipeline_result_state as module


def test_normalize_ui_state_applies_defaults_and_legacy_keys() -> None:
    normalized = module.normalize_ui_state(
        {
            "view_key": "tiles",
            "selected_index": 3,
        }
    )

    assert normalized == {
        "view_key": "content",
        "selected_index": 3,
    }

    fallback = module.normalize_ui_state({"view_key": "unknown", "selected_index": "x"})
    assert fallback == module.DEFAULT_UI_STATE


def test_load_and_persist_ui_state_delegate_to_storage(monkeypatch) -> None:
    monkeypatch.setattr(
        module,
        "load_all",
        lambda: {"ui_state": {"pipeline_results": {"view_key": "content", "selected_index": 4}}},
    )
    saved: list[dict[str, object]] = []
    monkeypatch.setattr(module, "save_all", lambda payload: saved.append(payload))

    state = module.load_ui_state()
    module.persist_ui_state(view_key="icon_m", selected_index=2)

    assert state == {"view_key": "content", "selected_index": 4}
    assert saved == [
        {
            "ui_state": {
                "pipeline_results": {
                    "view_key": "icon_m",
                    "selected_index": 2,
                }
            }
        }
    ]


def test_resolve_selected_index_prefers_pending_then_current() -> None:
    assert module.resolve_selected_index(length=0, pending_selected_index=2, selected_index=1) == (
        -1,
        2,
    )
    assert module.resolve_selected_index(length=5, pending_selected_index=3, selected_index=1) == (
        3,
        -1,
    )
    assert module.resolve_selected_index(length=5, pending_selected_index=-1, selected_index=4) == (
        4,
        -1,
    )
    assert module.resolve_selected_index(length=5, pending_selected_index=-1, selected_index=8) == (
        0,
        -1,
    )
