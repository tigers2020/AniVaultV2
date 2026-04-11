# Dataclass Contracts Consolidation Research

Date: 2026-04-10

## Background

- Public `@dataclass` types are currently split across `application/dto`, `domain/services`, and `interfaces/gui/models`.
- The largest duplication is the pipeline row shape:
  - `application.dto.match_result.MatchFileRow`
  - `interfaces.gui.models.ui_rows.PipelineRow`
- Title group sync also duplicates nearly the same structure across:
  - `domain.services.title_grouping.TitleGroupingInputRow`
  - `domain.services.title_grouping.TitleGroupMemberComputed`
  - `domain.services.title_grouping.TitleGroupComputed`
  - `application.dto.title_groups.TitleGroupMemberSync`
  - `application.dto.title_groups.TitleGroupSyncBundle`

## Current Findings

- `MatchFileRow` is imported across application, adapters, bootstrap, and GUI presenter code.
- GUI currently maintains a second row model with the same fields, then converts between the two in `interfaces/gui/presenters/row_mapper.py`.
- `application/dto/plan.py` mixes dataclasses with behavioral helpers such as group key/label derivation and `PathTemplateInput` conversion.
- Some dataclasses are true internal helpers and should stay local:
  - `adapters.persistence.sqlite.sqlite_library_index_repository._MediaFileUpsertRow`
  - `adapters.persistence.sqlite.sqlite_library_index_repository._ResolvedRootPath`
  - `bootstrap.container._SqliteRepositories`
  - `bootstrap.container._OrganizerDependencies`
  - `bootstrap.container._TmdbRuntime`
- Some dataclasses are domain or GUI-local value objects and should stay where they are:
  - `domain.models.ParsedInfo`
  - `domain.models.PathTemplateInput`
  - `domain.models.FileOperation`
  - `interfaces.gui.models.ui_rows.PipelineGroupRow`
  - `interfaces.gui.themes.base.ColorPalette`
  - `interfaces.gui.themes.responsive.DensityProfile`

## Consolidation Direction

- Add `src/anivault/contracts/` as the only source of truth for reusable public dataclasses.
- Move public dataclasses out of `application/dto` into workflow-oriented contract modules:
  - `pipeline.py`
  - `scan.py`
  - `parse.py`
  - `parse_cache.py`
  - `planning.py`
  - `library_index.py`
  - `organize_plan.py`
  - `title_groups.py`
  - `tmdb.py`
  - `progress.py`
  - `title_match.py`
- Rename shared types to neutral names:
  - `MatchFileRow` -> `PipelineRow`
  - `GroupMatchResultDTO` -> `GroupMatchResult`
  - `TmdbSeriesCandidateDTO` -> `TmdbSeriesCandidate`
  - `TitleGroupingInputRow` -> `TitleGroupingRow`
  - `TitleGroupMemberComputed` / `TitleGroupMemberSync` -> `TitleGroupMember`
  - `TitleGroupComputed` / `TitleGroupSyncBundle` -> `TitleGroupBundle`

## Behavior Changes Needed

- Pipeline row updates in TMDB hydration and persistence currently rebuild rows by passing 8 to 15 fields manually.
- Those updates should switch to `dataclasses.replace(...)` using shared contract objects.
- Title group computation should return the same bundle type that repositories persist, removing conversion glue from `sync_title_groups.py`.
- Planning helpers should move out of the contract module:
  - row grouping key/label logic belongs in a domain rule
  - `PipelineRow -> PathTemplateInput` conversion belongs near planning use-case logic

## Risks

- The current worktree already contains unrelated user changes in some of the same files touched by this refactor.
- Import sweep must be done carefully to avoid reverting those edits.
- Some tests and presenter modules may still assume the old `application.dto` module layout.

## Verification Target

- No `application.dto.*` imports remain in `src/`.
- No duplicate public row dataclasses remain.
- Title group compute and repository sync use the same bundle type.
- TMDB row update helpers use `replace(...)` instead of reconstructing every field manually.
