"""Regression tests for shared English i18n fragments."""

from __future__ import annotations

from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n.locales.en import MESSAGES
from anivault.interfaces.gui.i18n.locales.fragments import MOVE_FILES_EN, ORIGINAL_FILE_EN


def test_en_catalog_original_file_fragment_keys_stay_in_sync() -> None:
    original_file_keys = (
        K.TBL_ORIGINAL_FILE,
        K.DETAILS_LBL_ORIGINAL,
        K.CONTENT_LBL_ORIGINAL,
    )

    assert {MESSAGES[key] for key in original_file_keys} == {ORIGINAL_FILE_EN}


def test_en_catalog_move_files_fragment_keys_stay_in_sync() -> None:
    move_file_keys = (
        K.EXEC_CARD_HEADER_TITLE,
        K.EXEC_CARD_BTN_MOVE,
        K.DRY_RUN_BTN_APPLY,
    )

    assert {MESSAGES[key] for key in move_file_keys} == {MOVE_FILES_EN}
