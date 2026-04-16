# Episode Overview Dialog Plan

Status: Approved for implementation on 2026-04-12 based on the user-approved plan in the working thread.

## Summary
- Double-clicking an anime group card opens an episode overview dialog.
- The dialog fetches TMDB season episode data asynchronously through the existing presenter/coordinator worker pattern.
- Missing local episodes are shown with a translucent red overlay, and only existing files can be opened.

## Change Boundaries
- Add TMDB season overview DTOs and metadata port support.
- Extend TMDB adapter and container wiring for season overview execution.
- Add GUI parsing helpers, a new coordinator, a new dialog, and double-click signals from content/icon views.
- Add unit, GUI, adapter, and i18n coverage.

## Testing
- Episode and season parsing helpers
- Slot mapping and missing detection
- TMDB adapter success and `NotFound -> None`
- GUI double-click wiring and warning branches
- i18n catalog coverage
- Local smoke run via `python -m anivault`

## Approval Gate
- This document is the implementation gate record required by the project rules.
- Implementation may proceed from this plan revision.
