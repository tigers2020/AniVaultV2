# Plan: manual TMDB relay test coverage

## Scope

- Add a new focused unit test module for `ManualTmdbSearchRelay`.
- Reuse existing pytest + monkeypatch style used in `tests/unit/interfaces/gui`.
- Avoid production changes unless the current code proves untestable.

## Approach

1. Create lightweight dialog/presenter doubles instead of spinning full Qt widgets.
2. Patch `translate`, `QMessageBox.warning`, and `logger.warning` to assert observable behavior.
3. Cover valid result, invalid result, finish cleanup, and generic error-message paths.
4. Run the new target first, then run the repository validation pipeline in the required order.

## Approval

Automation run proceeding with this plan to add missing regression coverage for the latest merged GUI security path.
