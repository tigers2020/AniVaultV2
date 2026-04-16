# I18n Fragment Regression Research

## Context

- Latest merged commit `2d0c1b1` extracted repeated English strings into `src/anivault/interfaces/gui/i18n/locales/fragments.py`.
- Touched production files:
  - `src/anivault/interfaces/gui/i18n/locales/en.py`
  - `src/anivault/interfaces/gui/i18n/locales/fragments.py`
  - `src/anivault/interfaces/gui/i18n/locales/ko.py`
  - `src/anivault/constants/gui/components.py`

## Observations

- Existing GUI i18n tests cover language switching, parameter formatting, and one pipeline status translation.
- There is no focused regression test that locks the English catalog values for the keys switched to shared fragments.
- The changed keys appear in table labels, details/content labels, and execution/dry-run actions, so a fragment typo would affect multiple GUI surfaces at once.

## Risk

- `ORIGINAL_FILE_EN` now feeds multiple labels. A bad fragment value would silently break several labels together.
- `MOVE_FILES_EN` now feeds both the execution card and dry-run apply action. A mismatch would create inconsistent UI wording across the same flow.
- This is a low-volume but high-blast-radius regression target because the copied text is shared across organizer views.
