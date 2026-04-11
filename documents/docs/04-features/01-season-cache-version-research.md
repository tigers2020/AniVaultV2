# Season Cache Version Research

## Goal

Fix the case where a file that should be classified as season 2 appears as season 1 in the AniVault pipeline.

## Findings

- The current parser already extracts the season correctly for the reported filename.
  - Input: `[SubsPlease] The Beginning After the End S2 - 02 (1080p) [65B6C373].mkv`
  - `MinimalTitleParser.parse(...)` returns `season="2"`.
  - `AnitopyTitleParser.parse(...)` also returns `season="2"` and `episode="2"`.
- The stale-value risk is in the parse cache layer.
  - [`SqliteParseCacheRepository.get_valid_parses`](/F:/Python_Projects/AniVault_V2/src/anivault/adapters/persistence/sqlite/sqlite_parse_cache_repository.py) currently checks `parse_status` and `parse_input_signature`, but not `parser_version`.
  - Because of that, rows produced by an older parser can still be treated as valid cache hits even after parser behavior changes.
- The plan/path rendering layer still falls back to season 1 when season is blank.
  - [`_context_values`](/F:/Python_Projects/AniVault_V2/src/anivault/domain/services/path_template.py) uses `(row.season or "").strip() or "1"`.
  - That behavior is acceptable for truly unknown seasons, but it amplifies stale cached parse results by making old or empty season data look like a deliberate season 1 classification.

## Confirmed implementation target

- Add `parser_version == PARSER_VERSION` validation to parse-cache reads.
- Add an explicit parser test for the reported SubsPlease filename so season 2 stays locked by tests.
- Add a cache test proving that a matching signature is still a cache miss when the stored parser version is old.

## Risk notes

- This fix does not remove the season fallback of `"1"` in path rendering.
- Existing stale cache rows will be ignored after the change and replaced on the next successful parse.
