# GUI Layout Standardization Research

## Goal
- Bring the Qt GUI onto one desktop-first layout standard instead of page-by-page spacing and sizing decisions.
- Use Organizer as the reference layout and align shared shell and Settings patterns to it.

## Current Drift
- Shared layout metrics existed, but major screens still mixed token-based spacing with hard-coded values such as `18`, `14`, `12`, `8`, and `4`.
- `PanelHeader`, `StatCard`, `FolderScanBar`, `Topbar`, `ContentView`, `DetailsPane`, and `PipelineResultPanel` each carried separate padding and gap rules.
- Settings already reused some shared spacing helpers, while Organizer still relied on more local literals and fixed widths.
- The result was a UI that felt like multiple adjacent design systems rather than one Qt desktop shell.

## Chosen Standard
- Desktop-first Qt layout rules:
  - page shell uses a consistent outer gutter and page rhythm
  - command regions and data regions are visually separated by spacing, not arbitrary nesting
  - card/panel headers and card bodies share one padding system
  - split panes use responsive width tokens instead of scattered magic numbers
- QSS continues to handle theme and visual tone, while layout structure stays in Qt layouts and responsive helpers.

## Implementation Direction
- Extend `src/anivault/interfaces/gui/theme.py` with shared layout tokens for:
  - page section gap
  - card body padding
  - compact and inline control gaps
  - panel header padding and stack gap
  - sidebar/topbar spacing
  - results/detail pane width defaults
- Refactor Organizer to read as three regions:
  - command bar
  - summary stats
  - results workspace
- Reuse the same spacing system in shell and Settings so the app inherits one visual rhythm.

## Constraints
- Preserve presenter contracts and page wiring.
- Keep persisted settings keys unchanged.
- Avoid domain/application changes.
- Stay within the existing Atomic Design folder structure.
