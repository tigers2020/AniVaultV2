# Settings Dead Values Cleanup Plan

## Summary

Delete dead Settings values and the UI used to edit them, while keeping live settings and current Settings page structure intact.

## Scope

Remove these persisted keys and their UI:

- `parse_tmdb.video_extensions`
- `parse_tmdb.tmdb_search_mode`
- `scan_build.tmdb_mode`
- `scan_build.unknown_mode`

Remove these dead Settings-page controls:

- `ParseTmdbForm` fields for `Video extensions` and `TMDB search mode`
- `ScanBuildCard` combo boxes for `TMDB mode` and `Unknown mode`
- `ScanBuildCard` Settings action buttons for `Parse`, `Query TMDB`, and `Build Plan`

Keep these live settings/UI:

- `tmdb_api_key`
- `ignore_tokens`
- `season_folder_format`
- `target_root`
- `path_template`
- `unknown_resolution`
- `unknown_group_folder`
- `source_path`
- `auto_scan_on_first_show`
- appearance/theme controls
- save/reset/load controls

## Implementation steps

1. Update canonical settings schema in `src/anivault/constants/gui/settings.py`.
   - Remove dead keys and option lists.
   - Keep helper readers aligned with the reduced schema.
2. Update UI copy/constants in `src/anivault/constants/gui/components.py`.
   - Remove labels/button copy for deleted controls.
3. Simplify `ParseTmdbForm`.
   - Keep only API key, ignore tokens, and season folder format.
4. Simplify `ScanBuildCard`.
   - Keep source-path behavior.
   - Remove dead combo boxes.
   - Remove non-functional Settings-page action buttons except the actual scan action.
5. Update `SettingsPresenter`.
   - Stop reading/saving deleted keys.
   - Remove no-op handler surface that only existed for deleted UI where appropriate.
6. Update persistence/tests.
   - Make storage defaults and merge behavior reflect the reduced schema.
   - Rewrite presenter/widget tests to assert the new smaller payload shape.

## Tradeoffs

- This cleanup improves honesty of the Settings UI, but it removes dormant configuration keys from saved config.
- Old config files may still contain removed keys; we can safely ignore them on load rather than adding migration logic unless cleanup-on-save becomes necessary.

## Verification

- `pytest`
- `ruff check .`
- `mypy src`
- `black .`

## Approval request

Implementation should proceed only after explicit approval of this plan, per project gate rules.
