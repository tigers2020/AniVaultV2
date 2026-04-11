# Dataclass Contracts Consolidation Plan

Date: 2026-04-10

## Summary

- Introduce `src/anivault/contracts/` and move reusable public dataclasses there.
- Replace duplicated row and title-group dataclasses with shared contract types.
- Remove `application/dto` as a public dataclass package after import migration.

## Planned Changes

1. Create `anivault.contracts` modules and migrate public dataclass definitions.
2. Replace `MatchFileRow` and GUI `PipelineRow` with one shared `contracts.PipelineRow`.
3. Replace title-group computed and sync dataclasses with shared `TitleGroupingRow`, `TitleGroupMember`, and `TitleGroupBundle`.
4. Move planning helpers out of `application/dto/plan.py`.
5. Refactor TMDB and GUI row update code to use `dataclasses.replace(...)`.
6. Sweep imports across application, adapters, bootstrap, interfaces, and tests.
7. Remove legacy `application/dto` modules once all imports are updated.
8. Update docs and memo to record the new rule:
   reusable public dataclasses live in `anivault.contracts`, internal helper dataclasses stay local.

## Acceptance Criteria

- `src/anivault/contracts/` is the only reusable public dataclass package.
- `src/` contains zero `from anivault.application.dto` imports.
- `compute_title_groups()` returns shared bundles directly.
- GUI presenter flow, scan/parse/match/plan/apply flow, and SQLite adapters compile against the new contracts.
- Tests cover pipeline row continuity, title-group bundle continuity, and TMDB row updates.

## Verification

- `[테스]` updates or adds tests around shared contracts and refactored row behavior.
- `[렉스]` runs:
  - `pytest`
  - `ruff check .`
  - `mypy src`
  - `black .`
