# Refactor Batch 2026-04-09 Research

## Goal
- Reduce hidden coupling across the Organizer GUI flow without changing end-user behavior.
- Break the biggest maintenance hotspots into smaller seams that are easier to test.
- Introduce an app-scoped container so pages can share repository lifetime instead of each page building its own SQLite graph.

## Findings
- `interfaces/gui/presenters/organizing/*_coordinator.py` classes reach deep into `OrganizerPresenter` internals through many `self._p._...` accesses.
- `MatchFileRow <-> PipelineRow` conversion is duplicated across presenter/coordinator modules, which raises field-drift risk whenever UI or match DTO fields change.
- `application/use_cases/match_series.py` mixes scoring, provider search, cache lookups, persistence, and parallel orchestration in one module.
- `application/ports/title_match_port.py` is broad enough that most call sites only need part of the contract.
- `bootstrap/container.py` currently builds a fresh SQLite connection/lock/repository graph each time a page is created. `MainWindow` creates organizer and subtitle pages separately, so those flows do not share repository lifetime.
- Large SQLite repository classes contain reusable path/transaction helpers that can be extracted without changing query behavior.
- `interfaces/gui/templates/pipeline_result_panel.py` bundles UI-state normalization/persistence with rendering and selection synchronization.

## Decisions
- Keep public entry points stable where tests already rely on them.
- Add presenter facade/state methods instead of letting coordinators keep poking at private attributes directly.
- Extract reusable row-mapper helpers into a dedicated presenter-level module.
- Split `match_series` responsibilities into helper modules while keeping the existing top-level module as the compatibility surface.
- Introduce an app-scoped container for `MainWindow` and keep existing page factory functions as compatibility wrappers.
- Extract pure helpers from SQLite-heavy modules first instead of rewriting repository behavior wholesale in one pass.

## Guardrails
- No user-visible workflow changes in scan -> parse -> match -> dry-run/apply.
- Preserve current tests and existing public imports unless there is a strong reason to migrate them in the same patch.
- Keep Qt-thread behavior intact while improving access patterns around worker registration and state transitions.
