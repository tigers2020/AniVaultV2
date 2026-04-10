from pathlib import Path

from anivault.application.use_cases.hydrate_cached_tmdb_matches import make_execute
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_CACHED
from anivault.contracts.pipeline import MatchInput, PipelineRow
from anivault.contracts.title_groups import (
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)
from anivault.contracts.title_match import GroupTmdbMatchRecord, MatchStatus
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.tmdb_image_url import tmdb_poster_cdn_url


def _row(path: str) -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="Parsed",
        parse_group="Parsed",
        tmdb_korean_title_group="",
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="1",
        resolution="1080p",
        status="parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode="01",
    )


class _TitleGroups:
    def __init__(self, path_to_group: dict[str, int]) -> None:
        self.path_to_group = path_to_group
        self.bulk_lookups: list[list[str]] = []

    def load_rows_for_grouping(self, root_id: int) -> list[TitleGroupingRow]:
        """Unused by hydrate use case; satisfies TitleGroupRepository."""
        del root_id
        return []

    def get_group_id_for_path_norm(self, root_id: int, path_norm: str) -> int | None:
        del root_id
        return self.path_to_group.get(path_norm)

    def get_group_ids_for_path_norms(
        self,
        root_id: int,
        path_norms: list[str],
    ) -> dict[str, int]:
        del root_id
        self.bulk_lookups.append(list(path_norms))
        return {
            path_norm: self.path_to_group[path_norm]
            for path_norm in path_norms
            if path_norm in self.path_to_group
        }

    def replace_root_title_groups(self, root_id: int, bundles: list[TitleGroupBundle]) -> None:
        del root_id, bundles

    def replace_group_members(self, group_id: int, members: list[TitleGroupMember]) -> None:
        del group_id, members

    def list_title_groups_for_root(self, root_id: int) -> list[TitleGroupListRecord]:
        """Unused by hydrate use case; satisfies TitleGroupRepository."""
        _ = root_id
        empty: list[TitleGroupListRecord] = []
        return empty

    def get_group_id(self, root_id: int, group_key: str) -> int | None:
        del root_id, group_key
        return None


class _TitleMatch:
    def __init__(
        self,
        *,
        matches: dict[int, GroupTmdbMatchRecord] | None = None,
        candidates: dict[int, TmdbSeriesCandidate] | None = None,
        poster_paths: dict[tuple[int, str, str], str] | None = None,
    ) -> None:
        self.matches = matches or {}
        self.candidates = candidates or {}
        self.poster_paths = poster_paths or {}
        self.poster_lookup_count: dict[tuple[int, str, str], int] = {}

    def get_search_cache_json(self, cache_key: str) -> str | None:
        del cache_key
        return None

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
    ) -> None:
        del cache_key, language, normalized_query, year_hint, page, response_json, expires_at

    def invalidate_search(self, cache_key: str) -> None:
        del cache_key

    def upsert_series(
        self,
        candidate: TmdbSeriesCandidate,
        *,
        raw_json: str,
        expires_at: str,
    ) -> None:
        del candidate, raw_json, expires_at

    def get_group_match(self, group_id: int) -> GroupTmdbMatchRecord | None:
        return self.matches.get(group_id)

    def get_group_matches(self, group_ids: list[int]) -> dict[int, GroupTmdbMatchRecord]:
        return {
            group_id: self.matches[group_id] for group_id in group_ids if group_id in self.matches
        }

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidate | None:
        return self.candidates.get(tmdb_id)

    def get_series_candidates(self, tmdb_ids: list[int]) -> dict[int, TmdbSeriesCandidate]:
        return {
            tmdb_id: self.candidates[tmdb_id] for tmdb_id in tmdb_ids if tmdb_id in self.candidates
        }

    def find_series_candidates_by_title(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> list[TmdbSeriesCandidate]:
        del query, limit
        return []

    def set_group_match(
        self,
        group_id: int,
        tmdb_id: int,
        match_status: MatchStatus,
        match_score: float | None,
    ) -> None:
        del group_id, tmdb_id, match_status, match_score

    def invalidate_group_match(self, group_id: int) -> None:
        del group_id

    def get_poster_local_path(
        self,
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
    ) -> str | None:
        key = (tmdb_id, image_kind, remote_path)
        self.poster_lookup_count[key] = self.poster_lookup_count.get(key, 0) + 1
        return self.poster_paths.get((tmdb_id, image_kind, remote_path))

    def save_poster_asset(
        self,
        tmdb_id: int,
        image_kind: str,
        remote_path: str,
        *,
        local_path: str,
        status: str,
        verified_at: str | None,
    ) -> None:
        del tmdb_id, image_kind, remote_path, local_path, status, verified_at


def test_hydrate_cached_tmdb_matches_uses_series_and_local_poster(tmp_path: Path) -> None:
    media = str(tmp_path / "show.mkv")
    poster = tmp_path / "poster.jpg"
    poster.write_bytes(b"jpg")
    group_id = 10
    tmdb_id = 123
    candidate = TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Korean Title",
        original_name="Original Title",
        first_air_date="2025-04-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
        popularity=1.0,
    )
    execute = make_execute(
        title_match=_TitleMatch(
            matches={
                group_id: GroupTmdbMatchRecord(
                    group_id=group_id,
                    tmdb_id=tmdb_id,
                    match_status="confirmed",
                    match_score=None,
                )
            },
            candidates={tmdb_id: candidate},
            poster_paths={(tmdb_id, "poster", "/poster.jpg"): str(poster)},
        ),
        title_groups=_TitleGroups({normalize_path_key(media): group_id}),
    )

    result = execute(MatchInput(files=(_row(media),), index_root_id=1))

    hydrated = result.files[0]
    assert hydrated.tmdb_korean_title_group == "Korean Title"
    assert hydrated.tmdb_series_id == "123"
    assert hydrated.tmdb_poster_path == "/poster.jpg"
    assert hydrated.tmdb_backdrop_path == "/backdrop.jpg"
    assert hydrated.year == "2025"
    assert hydrated.poster_url == str(poster)
    assert hydrated.backdrop_url.endswith("/backdrop.jpg")
    assert hydrated.status == PIPELINE_ROW_STATUS_TMDB_CACHED


def test_hydrate_cached_tmdb_matches_falls_back_to_cdn_on_missing_local_poster(
    tmp_path: Path,
) -> None:
    media = str(tmp_path / "show.mkv")
    group_id = 10
    tmdb_id = 123
    candidate = TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Korean Title",
        original_name="Original Title",
        first_air_date="2025-04-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    execute = make_execute(
        title_match=_TitleMatch(
            matches={
                group_id: GroupTmdbMatchRecord(
                    group_id=group_id,
                    tmdb_id=tmdb_id,
                    match_status="auto_matched",
                    match_score=0.9,
                )
            },
            candidates={tmdb_id: candidate},
        ),
        title_groups=_TitleGroups({normalize_path_key(media): group_id}),
    )

    result = execute(MatchInput(files=(_row(media),), index_root_id=1))

    assert result.files[0].poster_url == tmdb_poster_cdn_url("/poster.jpg")


def test_hydrate_cached_tmdb_matches_applies_hit_to_whole_current_group(
    tmp_path: Path,
) -> None:
    cached_media = str(tmp_path / "show-01.mkv")
    uncached_media = str(tmp_path / "show-02.mkv")
    group_id = 10
    tmdb_id = 123
    candidate = TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Korean Title",
        original_name="Original Title",
        first_air_date="2025-04-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    execute = make_execute(
        title_match=_TitleMatch(
            matches={
                group_id: GroupTmdbMatchRecord(
                    group_id=group_id,
                    tmdb_id=tmdb_id,
                    match_status="confirmed",
                    match_score=None,
                )
            },
            candidates={tmdb_id: candidate},
        ),
        title_groups=_TitleGroups({normalize_path_key(cached_media): group_id}),
    )

    result = execute(
        MatchInput(
            files=(_row(cached_media), _row(uncached_media)),
            index_root_id=1,
        )
    )

    assert [r.tmdb_series_id for r in result.files] == ["123", "123"]
    assert [r.tmdb_korean_title_group for r in result.files] == [
        "Korean Title",
        "Korean Title",
    ]


def test_hydrate_cached_tmdb_matches_uses_later_path_hit_for_same_current_group(
    tmp_path: Path,
) -> None:
    missed_media = str(tmp_path / "show-00.mkv")
    cached_media = str(tmp_path / "show-01.mkv")
    group_id = 10
    tmdb_id = 123
    candidate = TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Korean Title",
        original_name="Original Title",
        first_air_date="2025-04-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    execute = make_execute(
        title_match=_TitleMatch(
            matches={
                group_id: GroupTmdbMatchRecord(
                    group_id=group_id,
                    tmdb_id=tmdb_id,
                    match_status="confirmed",
                    match_score=None,
                )
            },
            candidates={tmdb_id: candidate},
        ),
        title_groups=_TitleGroups({normalize_path_key(cached_media): group_id}),
    )

    result = execute(
        MatchInput(
            files=(_row(missed_media), _row(cached_media)),
            index_root_id=1,
        )
    )

    assert [r.tmdb_series_id for r in result.files] == ["123", "123"]
    assert [r.tmdb_korean_title_group for r in result.files] == [
        "Korean Title",
        "Korean Title",
    ]


def test_hydrate_cached_tmdb_matches_leaves_rows_unchanged_on_cache_miss(tmp_path: Path) -> None:
    media = str(tmp_path / "show.mkv")
    row = _row(media)
    execute = make_execute(
        title_match=_TitleMatch(),
        title_groups=_TitleGroups({}),
    )

    result = execute(MatchInput(files=(row,), index_root_id=1))

    assert result.files == (row,)


def test_hydrate_cached_tmdb_matches_ignores_rejected_match(tmp_path: Path) -> None:
    media = str(tmp_path / "show.mkv")
    row = _row(media)
    group_id = 10
    execute = make_execute(
        title_match=_TitleMatch(
            matches={
                group_id: GroupTmdbMatchRecord(
                    group_id=group_id,
                    tmdb_id=123,
                    match_status="rejected",
                    match_score=None,
                )
            }
        ),
        title_groups=_TitleGroups({normalize_path_key(media): group_id}),
    )

    result = execute(MatchInput(files=(row,), index_root_id=1))

    assert result.files == (row,)


def test_hydrate_cached_tmdb_matches_memoizes_poster_lookup_for_shared_candidate(
    tmp_path: Path,
) -> None:
    media_a = str(tmp_path / "show-01.mkv")
    media_b = str(tmp_path / "show-02.mkv")
    poster = tmp_path / "poster.jpg"
    poster.write_bytes(b"jpg")
    group_id = 10
    tmdb_id = 123
    candidate = TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko="Korean Title",
        original_name="Original Title",
        first_air_date="2025-04-01",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    title_match = _TitleMatch(
        matches={
            group_id: GroupTmdbMatchRecord(
                group_id=group_id,
                tmdb_id=tmdb_id,
                match_status="confirmed",
                match_score=None,
            )
        },
        candidates={tmdb_id: candidate},
        poster_paths={(tmdb_id, "poster", "/poster.jpg"): str(poster)},
    )
    execute = make_execute(
        title_match=title_match,
        title_groups=_TitleGroups(
            {
                normalize_path_key(media_a): group_id,
                normalize_path_key(media_b): group_id,
            }
        ),
    )

    result = execute(MatchInput(files=(_row(media_a), _row(media_b)), index_root_id=1))

    assert [row.poster_url for row in result.files] == [str(poster), str(poster)]
    assert title_match.poster_lookup_count == {(tmdb_id, "poster", "/poster.jpg"): 1}
