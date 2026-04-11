# Settings Schema and Layout Cleanup Plan

## Scope
- Consolidate Settings schema definitions around `src/anivault/constants/gui/settings.py`.
- Update Settings widgets and persistence helpers to consume that schema.
- Normalize Settings page and Settings card spacing with shared responsive helpers.

## Implementation Steps
1. Add canonical schema helper functions to `constants/gui/settings.py`.
2. Remove persisted defaults and saved-option lists from copy/example modules.
3. Update `settings_storage.py` to build defaults from the canonical schema helpers.
4. Update Settings widgets to read defaults and options from `constants/gui/settings.py`.
5. Add shared Settings spacing helpers in `interfaces/gui/theme.py`.
6. Refactor Settings page and cards to use those helpers without changing card order.
7. Extend unit tests for canonical defaults, presenter wiring, and new spacing helpers.

## Verification
- `pytest`
- `ruff check .`
- `mypy src`
- `black .`

## Guardrails
- Do not redesign Organizer layout in this pass.
- Do not touch the unrelated user change in `tests/unit/application/test_sync_title_groups_extra.py`.
- Report separately if `black .` rewrites files.
