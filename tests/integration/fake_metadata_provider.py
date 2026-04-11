"""Test doubles for integration tests (no network)."""

from __future__ import annotations

from collections.abc import Sequence

from anivault.contracts.tmdb import TmdbSeriesCandidate


class FakeMetadataProvider:
    """Minimal MetadataProvider returning one deterministic candidate per query."""

    def search_series(
        self,
        query: str,
        *,
        year: int | None = None,
    ) -> Sequence[TmdbSeriesCandidate]:
        del year
        tmdb_id = 424242
        return (
            TmdbSeriesCandidate(
                tmdb_id=tmdb_id,
                name_ko=f"{query} (KO)",
                original_name=query,
                first_air_date="2024-01-01",
                original_language="ja",
                overview="",
                poster_path="/poster.jpg",
                backdrop_path="/backdrop.jpg",
                popularity=10.0,
            ),
        )
