# GUI Layout Standardization Plan

## Summary
- Introduce a shared GUI layout token layer in `theme.py`.
- Apply the new tokens to Organizer first, then align shell and Settings to the same spacing and width system.
- Keep behavior, data flow, and persisted settings unchanged.

## Target Areas
- Shared widgets:
  - `PanelHeader`
  - `StatCard`
  - `FolderScanBar`
  - `Topbar`
  - `Sidebar`
  - `ContentView`
  - `DetailsPane`
  - `PipelineResultPanel`
- Pages:
  - `OrganizerPage`
  - `SettingsPage`
  - `MainShell`

## Risks
- GUI smoke tests may rely on previous spacing assumptions.
- Splitter and minimum-width changes may affect density-sensitive tests.
- Fixed-height widgets may need minor follow-up tuning after visual verification.

## Rollout
1. Add research and plan artifacts in `docs/`.
2. Add standardized layout tokens in `src/anivault/interfaces/gui/theme.py`.
3. Update shared Organizer-facing widgets to consume the new tokens.
4. Align shell and Settings spacing with the same system.
5. Extend GUI tests for the new layout helpers and Organizer structure.
6. Run `pytest`, `ruff check .`, `mypy src`, and `black .`.
