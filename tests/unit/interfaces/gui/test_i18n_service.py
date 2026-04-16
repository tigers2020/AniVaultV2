"""Tests for GUI i18n service and catalog."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from anivault.constants.gui.components import SCAN_PARSE_COORDINATOR_STATUS_SCANNED
from anivault.interfaces.gui.i18n import (
    get_i18n_service,
    init_i18n_from_settings,
    translate,
    translate_pipeline_status,
)
from anivault.interfaces.gui.i18n.keys import (
    CONTENT_LBL_ORIGINAL,
    DETAILS_LBL_ORIGINAL,
    DLG_EP_OVERVIEW_LOADING,
    DRY_RUN_BTN_APPLY,
    EXEC_CARD_BTN_MOVE,
    EXEC_CARD_HEADER_TITLE,
    ORG_EP_OVERVIEW_MATCH_REQUIRED_TITLE,
    ORG_PLAN_COMPLETE_MESSAGE,
    SHELL_TAB_SUBTITLES,
    TBL_ORIGINAL_FILE,
)


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_translate_ko_and_en(qapp: QApplication) -> None:
    svc = get_i18n_service()
    svc.set_current_language("ko", emit_signal=False)
    ko_text = translate(SHELL_TAB_SUBTITLES)
    svc.set_current_language("en", emit_signal=False)
    en_text = translate(SHELL_TAB_SUBTITLES)
    assert ko_text == "자막만"
    assert en_text == "Subtitles only"


def test_translate_format_params(qapp: QApplication) -> None:
    get_i18n_service().set_current_language("en", emit_signal=False)
    out = translate(ORG_PLAN_COMPLETE_MESSAGE, moved_count=3)
    assert "3" in out
    assert "file" in out.lower()


def test_translate_en_fragment_backed_labels(qapp: QApplication) -> None:
    get_i18n_service().set_current_language("en", emit_signal=False)

    assert translate(TBL_ORIGINAL_FILE) == "Original file"
    assert translate(DETAILS_LBL_ORIGINAL) == "Original file"
    assert translate(CONTENT_LBL_ORIGINAL) == "Original file"

    assert translate(EXEC_CARD_HEADER_TITLE) == "Move files"
    assert translate(EXEC_CARD_BTN_MOVE) == "Move files"
    assert translate(DRY_RUN_BTN_APPLY) == "Move files"


def test_translate_episode_overview_keys_exist_in_both_languages(qapp: QApplication) -> None:
    svc = get_i18n_service()
    svc.set_current_language("en", emit_signal=False)
    assert "TMDB" in translate(DLG_EP_OVERVIEW_LOADING)
    assert translate(ORG_EP_OVERVIEW_MATCH_REQUIRED_TITLE) == "TMDB match required"

    svc.set_current_language("ko", emit_signal=False)
    assert translate(DLG_EP_OVERVIEW_LOADING)
    assert translate(ORG_EP_OVERVIEW_MATCH_REQUIRED_TITLE)


def test_set_current_language_emits_once(qapp: QApplication) -> None:
    svc = get_i18n_service()
    svc.set_current_language("ko", emit_signal=False)
    received: list[str] = []
    svc.language_changed.connect(lambda code: received.append(code))
    svc.set_current_language("en", emit_signal=True)
    svc.set_current_language("en", emit_signal=True)
    assert received == ["en"]


def test_init_i18n_from_settings(monkeypatch: pytest.MonkeyPatch, qapp: QApplication) -> None:
    monkeypatch.setattr(
        "anivault.interfaces.gui.settings_storage.load_all",
        lambda: {"language": "en"},
    )
    init_i18n_from_settings(emit_signal=False)
    assert get_i18n_service().get_current_language() == "en"


def test_translate_pipeline_status_known_and_unknown(qapp: QApplication) -> None:
    svc = get_i18n_service()
    svc.set_current_language("ko", emit_signal=False)
    assert translate_pipeline_status(SCAN_PARSE_COORDINATOR_STATUS_SCANNED) == "스캔됨"
    svc.set_current_language("en", emit_signal=False)
    assert translate_pipeline_status(SCAN_PARSE_COORDINATOR_STATUS_SCANNED) == "Scanned"
    assert translate_pipeline_status("unknown-status-xyz") == "unknown-status-xyz"


def test_normalize_unknown_language_in_init(
    monkeypatch: pytest.MonkeyPatch, qapp: QApplication
) -> None:
    monkeypatch.setattr(
        "anivault.interfaces.gui.settings_storage.load_all",
        lambda: {"language": "xx"},
    )
    init_i18n_from_settings(emit_signal=False)
    assert get_i18n_service().get_current_language() == "ko"
