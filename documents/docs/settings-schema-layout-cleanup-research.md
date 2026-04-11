# Settings Schema and Layout Cleanup Research

## Goal
- Remove drift between persisted settings definitions and Settings UI defaults.
- Replace hard-coded Settings page spacing with shared responsive layout helpers.

## Findings
- Persisted settings defaults already lived in `src/anivault/constants/gui/settings.py`, but several Settings widgets duplicated those values through `src/anivault/constants/gui/components.py`.
- Settings option lists were split across modules:
  - scan/build option lists in `components.py`
  - TMDB search modes in `forms.py`
- `src/anivault/interfaces/gui/settings_storage.py` manually rebuilt the default payload instead of reusing a canonical schema helper.
- Settings layout spacing used repeated literals like `10`, `14`, and `18` across the page and card components.

## Decisions
- `src/anivault/constants/gui/settings.py` becomes the single source of truth for:
  - persisted keys
  - persisted defaults
  - saved-option lists used by Settings forms
- `src/anivault/constants/gui/components.py` remains UI-copy-only.
- `src/anivault/constants/gui/forms.py` keeps example-only constants.
- Shared Settings spacing helpers live in `src/anivault/interfaces/gui/theme.py` and are backed by the responsive density profile.

## Compatibility Constraints
- Do not rename persisted config keys.
- Keep `.env`-only handling for `tmdb_api_key`.
- Preserve fallback behavior for invalid `ui_state.pipeline_results`.
- Preserve migration from `scan_build.target_path` to `path_rules.target_root`.
