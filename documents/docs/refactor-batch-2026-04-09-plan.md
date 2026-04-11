# Refactor Batch 2026-04-09 Plan

## Scope
- Refactor organizer presenter/coordinator collaboration through explicit facade methods.
- Centralize `PipelineRow` and `MatchFileRow` mapping logic.
- Split `match_series` into scoring/search/persistence helpers and narrow the `TitleMatchRepository` contract into smaller protocols.
- Add an app-scoped container used by `MainWindow`.
- Extract small helper modules from large SQLite/result-panel modules where behavior can remain stable.
- Add regression tests around the new seams.

## Implementation Steps
1. Add research-backed batch docs in `docs/`.
2. Introduce presenter row-mapper helpers and update presenter/coordinators to use them.
3. Add presenter facade/state helpers so coordinator code stops depending on raw `_p._...` access patterns.
4. Split `match_series` helper responsibilities into dedicated modules and keep `match_series.py` as the public compatibility surface.
5. Narrow `title_match_port.py` with smaller protocols and use them in helper modules.
6. Add an app-scoped container and switch `MainWindow` to it while preserving existing factory helpers.
7. Extract selected helper modules from SQLite/result-panel hotspots without changing query semantics.
8. Add/adjust unit tests for the new seams and rerun the verification pipeline.

## Verification
- `pytest`
- `ruff check .`
- `mypy src`
- `black --check .`

## Constraints
- Do not redesign the GUI layout.
- Do not change the scan/match/apply workflow semantics.
- Keep `black .` out of this pass unless formatting is explicitly needed after edits.
