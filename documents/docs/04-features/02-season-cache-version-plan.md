# Season Cache Version Plan

## Summary

Prevent stale parse cache rows from overriding newer parser behavior, and lock the reported season 2 filename into adapter tests.

## Implementation Steps

1. Update parse-cache read validation in `src/anivault/adapters/persistence/sqlite/sqlite_parse_cache_repository.py`.
   - Read `parser_version` alongside the cached row.
   - Treat rows as valid only when status is OK, signature matches, and stored parser version equals `PARSER_VERSION`.
2. Keep parse use-case flow unchanged.
   - Let version-mismatched cache rows fall through as normal cache misses so the existing parse path repopulates them.
3. Extend `tests/unit/adapters/test_title_parser_extra.py`.
   - Add a regression test for `[SubsPlease] The Beginning After the End S2 - 02 (1080p) [65B6C373]`.
   - Assert season `2`, episode `2`, and stable title parsing.
4. Extend `tests/unit/adapters/test_sqlite_parse_cache_repository.py`.
   - Add a regression test showing that a row with the correct signature but an old `parser_version` is not returned as a valid cache hit.

## Verification

- `pytest tests/unit/adapters/test_title_parser_extra.py`
- `pytest tests/unit/adapters/test_sqlite_parse_cache_repository.py`
- `pytest`
- `ruff check .`
- `mypy src`
- `black .`

## Assumptions

- The user-visible season 1 symptom is caused by stale cached parse data rather than the current parser implementation.
- The default season fallback of `"1"` in path rendering remains unchanged in this task.
