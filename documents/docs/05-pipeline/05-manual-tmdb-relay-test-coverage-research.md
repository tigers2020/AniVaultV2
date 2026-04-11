# Research: manual TMDB relay test coverage

## Date

2026-04-10

## Scope

- Recent merged commit inspected: `2f95f01` (`[security] Harden TMDB image URLs and manual search error UI`)
- Production target: `src/anivault/interfaces/gui/presenters/organizing/manual_tmdb_relay.py`
- Existing tests found for related flow: `tests/unit/interfaces/gui/test_match_coordinator.py`

## Findings

1. `ManualTmdbSearchRelay.on_error()` changed behavior in the latest security commit.
It now logs the exception and shows a generic translated error message instead of exposing `str(exc)`.

2. No focused unit test covers the relay itself.
The coordinator tests only stub `ManualTmdbSearchRelay` when starting the worker, so regressions inside `on_result()`, `on_finished()`, and `on_error()` would not be caught.

3. Risk is meaningful because this path sits on a user-triggered fallback flow.
If it regresses, the manual TMDB search dialog can stay busy forever, leak raw exception text to users, or fail to clear candidates for malformed results.

## Test targets

- `on_result()` accepts only `list`/`tuple` collections fully composed of `TmdbSeriesCandidate`.
- `on_result()` clears candidates when payload shape is invalid.
- `on_finished()` clears busy state and schedules relay cleanup.
- `on_error()` clears busy state, logs the failure, and shows translated generic title/message.
