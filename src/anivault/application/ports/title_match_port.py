"""Ports for TMDB cache and title match persistence."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.contracts.title_match import GroupTmdbMatchRecord, MatchStatus
from anivault.contracts.tmdb import TmdbSeriesCandidate


@runtime_checkable
class SearchCacheRepository(Protocol):
    def get_search_cache_json(self, cache_key: str) -> str | None: ...

    def put_search_cache(
        self,
        cache_key: str,
        *,
        language: str,
        normalized_query: str,
        year_hint: int | None,
        page: int,
        response_json: str,
        expires_at: str,
    ) -> None: ...

    def invalidate_search(self, cache_key: str) -> None: ...


@runtime_checkable
class TmdbSeriesRepository(Protocol):
    def upsert_series(
        self,
        candidate: TmdbSeriesCandidate,
        *,
        raw_json: str,
        expires_at: str,
    ) -> None: ...

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidate | None: ...

    def get_series_candidates(self, tmdb_ids: list[int]) -> dict[int, TmdbSeriesCandidate]: ...

    def find_series_candidates_by_title(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[TmdbSeriesCandidate]: ...


@runtime_checkable
class GroupMatchRepository(Protocol):
    def get_group_match(self, group_id: int) -> GroupTmdbMatchRecord | None: ...

    def get_group_matches(self, group_ids: list[int]) -> dict[int, GroupTmdbMatchRecord]: ...

    def set_group_match(
        self,
        group_id: int,
        tmdb_id: int,
        match_status: MatchStatus,
        match_score: float | None,
    ) -> None: ...

    def invalidate_group_match(self, group_id: int) -> None: ...


@runtime_checkable
class PosterAssetRepository(Protocol):
    def get_poster_local_path(
        self,
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
    ) -> str | None: ...

    def save_poster_asset(
        self,
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
        *,
        local_path: str,
        status: str,
        verified_at: str | None,
    ) -> None: ...


@runtime_checkable
class TitleMatchRepository(
    SearchCacheRepository,
    TmdbSeriesRepository,
    GroupMatchRepository,
    PosterAssetRepository,
    Protocol,
):
    """Combined repository contract for title match persistence."""
