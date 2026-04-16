# I18n Fragment Regression Plan

## Goal

Add a minimal regression test that proves the extracted English fragments still produce the expected organizer copy.

## Scope

- Update `tests/unit/interfaces/gui/test_i18n_service.py`.

## Test additions

- Assert the English catalog returns `"Original file"` for:
  - `TBL_ORIGINAL_FILE`
  - `DETAILS_LBL_ORIGINAL`
  - `CONTENT_LBL_ORIGINAL`
- Assert the English catalog returns `"Move files"` for:
  - `EXEC_CARD_HEADER_TITLE`
  - `EXEC_CARD_BTN_MOVE`
  - `DRY_RUN_BTN_APPLY`

## Why this shape

- It directly targets the keys changed in `2d0c1b1`.
- It avoids fragile widget construction and stays deterministic at the catalog/service layer.
- It covers the shared-fragment blast radius with one small test.
