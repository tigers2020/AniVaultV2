"""Port for metadata providers such as TMDB."""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from anivault.contracts.tmdb import TmdbSeriesCandidate, TvSeasonOverview


@runtime_checkable
class MetadataProvider(Protocol):
    """Contract for series metadata search."""

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidate]: ...

    def tv_season_overview(self, tv_id: int, season_number: int) -> TvSeasonOverview | None: ...
