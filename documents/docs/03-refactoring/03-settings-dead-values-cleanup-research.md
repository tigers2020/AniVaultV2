# Settings Dead Values Cleanup Research

## Goal

Remove Settings values that are displayed and persisted but do not affect runtime behavior, along with UI that only exists to edit those dead values.

## Confirmed live settings

- `parse_tmdb.ignore_tokens`
  - Used when creating the filename parser in [container.py](/F:/Python_Projects/AniVault_V2/src/anivault/bootstrap/container.py).
  - Passed into `AnitopyTitleParser(ignore_tokens=...)`.
- `path_rules.unknown_group_folder`
  - Used when building `PlanInput` in [plan_helpers.py](/F:/Python_Projects/AniVault_V2/src/anivault/interfaces/gui/presenters/plan_helpers.py).
  - Used as the fallback group folder name in [path_template.py](/F:/Python_Projects/AniVault_V2/src/anivault/domain/services/path_template.py).
- `path_rules.unknown_resolution`
  - Used in the same planning/path-rendering flow.
- `scan_build.source_path`
  - Used by Organizer auto-scan and apply/log-root fallback.
- `scan_build.auto_scan_on_first_show`
  - Used by Organizer first-show behavior.
- `parse_tmdb.tmdb_api_key`
  - Stored in `.env` and used to enable TMDB-backed behavior.
- `parse_tmdb.season_folder_format`
  - Still present in schema/UI, but current implementation should be re-checked before removal because it looks intended for path rendering semantics and was not part of the explicit dead-value request.

## Confirmed dead settings

These are currently rendered in Settings and saved in config, but no runtime path consumes them outside UI/storage/tests.

- `parse_tmdb.video_extensions`
  - Appears in `ParseTmdbForm`.
  - Not used by scan, parse, subtitle pairing, or bootstrap wiring.
  - Runtime video extension handling currently comes from domain/bootstrap constants instead.
- `parse_tmdb.tmdb_search_mode`
  - Appears in `ParseTmdbForm`.
  - Not used by TMDB search execution or metadata provider wiring.
- `scan_build.tmdb_mode`
  - Appears in `ScanBuildCard`.
  - Not used by Organizer scan/match flow.
- `scan_build.unknown_mode`
  - Appears in `ScanBuildCard`.
  - Not used by planning or file movement behavior.

## Dead UI candidates

The following UI appears non-functional or redundant in the current Settings page context.

- `ParseTmdbForm` controls for:
  - `Video extensions`
  - `TMDB search mode`
- `ScanBuildCard` controls for:
  - `TMDB mode`
  - `Unknown mode`
- `ScanBuildCard` action buttons in Settings:
  - `Parse`
  - `Query TMDB`
  - `Build Plan`
  - In `SettingsPresenter`, corresponding handlers are stubs (`pass`) and do not trigger behavior.

## Likely affected files

- Schema/storage:
  - `src/anivault/constants/gui/settings.py`
  - `src/anivault/interfaces/gui/settings_storage.py`
- Settings UI:
  - `src/anivault/constants/gui/components.py`
  - `src/anivault/interfaces/gui/components/organisms/parse_tmdb_form.py`
  - `src/anivault/interfaces/gui/components/organisms/scan_build_card.py`
  - `src/anivault/interfaces/gui/presenters/settings_presenter.py`
- Tests:
  - `tests/unit/interfaces/gui/test_app_main_page_settings_presenter.py`
  - `tests/unit/interfaces/gui/test_settings_storage.py`
  - `tests/unit/interfaces/gui/test_widget_smoke.py`
  - possibly `tests/unit/bootstrap/test_container_extra.py` only if schema constants/imports shift

## Risks

- Removing fields from defaults and persistence can break tests that still expect the old saved payload shape.
- If any future-but-not-yet-wired feature was depending on these stored keys informally, removal will erase that dormant compatibility path.
- `ScanBuildCard` is reused on the Settings page only in current wiring, but the component should still be checked for any hidden cross-page reuse before trimming UI aggressively.
