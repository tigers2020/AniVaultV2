# Episode Overview Dialog Research

## Scope
- TMDB season lookup signature in `tmdbapis`
- Returned season object shape needed for episode overview UI
- Error type used for missing seasons

## Findings
- `tmdbapis.TMDbAPIs.tv_season(tv_id: int, season_number: int, load: bool = True, partial: bool | str | None = False) -> tmdbapis.objs.reload.Season`
- `tmdbapis.objs.reload.Season` exposes `episodes` as a list of episode objects loaded from TMDB season details.
- The same call documents and raises `tmdbapis.exceptions.NotFound` when the season is not found for the given TMDB TV id and season number.
- Existing AniVault TMDB client already imports and handles `NotFound` for `search_tv_raw`, so the same exception type can be reused for season lookup.

## Implementation Notes
- A small normalized DTO is preferable to returning raw `Season` objects across layers.
- The provider should translate `NotFound` into `None` for the new season overview port method.
- Other exceptions should continue through the worker error path so the GUI can show a warning instead of silently treating them as an empty season.
