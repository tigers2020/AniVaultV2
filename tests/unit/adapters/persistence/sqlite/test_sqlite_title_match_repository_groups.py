from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_title_group_repository import (
    SqliteTitleGroupRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_title_match_repository import (
    SqliteTitleMatchRepository,
)
from anivault.application.dto.library_index import BulkMediaUpsertItem
from anivault.application.dto.title_groups import TitleGroupMemberSync, TitleGroupSyncBundle
from anivault.constants.application.statuses import (
    MATCH_STATUS_CONFIRMED,
    MATCH_STATUS_REJECTED,
)
from anivault.domain.media.extensions import classify_media_kind


def _candidate(tmdb_id: int, name_ko: str = "Frieren"):
    from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO

    return TmdbSeriesCandidateDTO(
        tmdb_id=tmdb_id,
        name_ko=name_ko,
        original_name="Sousou no Frieren",
        first_air_date="2023-09-29",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
        popularity=1.0,
    )


def _seed_title_match_repo(tmp_path: Path) -> tuple[object, SqliteTitleMatchRepository, int]:
    db_path = tmp_path / "title-match.db"
    library_root = tmp_path / "library"
    media_path = library_root / "show-01.mkv"
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"media")
    conn = create_connection(db_path)
    lock = threading.Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    title_groups = SqliteTitleGroupRepository(conn, lock)
    repo = SqliteTitleMatchRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))
    scan_id = library_index.begin_scan(root_id, "test")
    library_index.upsert_media_files(
        root_id,
        scan_id,
        [BulkMediaUpsertItem(str(media_path), classify_media_kind(media_path))],
    )
    media = library_index.resolve_media_for_parse(root_id, [str(media_path)])[0]
    assert media is not None
    conn.execute(
        """
        INSERT INTO parse_cache (
            media_file_id, parser_version, parse_input_signature, parse_status, dto_json,
            parsed_title, parsed_title_normalized, parsed_year,
            season_number, episode_start, episode_end, episode_count,
            confidence, error_code, error_message, created_at, updated_at
        ) VALUES (?, 'v1', 'sig-1', 'ok', '{}', 'Show', 'show', 2024, 1, 1, NULL, NULL, NULL, NULL, NULL, ?, ?)
        """,
        (media.id, "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
    )
    conn.commit()
    title_groups.replace_root_title_groups(
        root_id,
        [
            TitleGroupSyncBundle(
                group_key="Show",
                group_type="parsed_title_norm",
                canonical_title="Show",
                canonical_title_normalized="show",
                tmdb_series_id=None,
                group_confidence=0.9,
                members=(TitleGroupMemberSync(media.id, "primary_video", 0.9),),
            )
        ],
    )
    group_id = title_groups.get_group_id(root_id, "Show")
    assert group_id is not None
    return conn, repo, group_id


def test_title_match_repository_group_match_lifecycle_and_bulk_reads(tmp_path: Path) -> None:
    conn, repo, group_id = _seed_title_match_repo(tmp_path)
    try:
        confirmed = _candidate(101)
        repo.upsert_series(
            confirmed,
            raw_json=json.dumps(asdict(confirmed), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        rejected_seed = _candidate(202)
        repo.upsert_series(
            rejected_seed,
            raw_json=json.dumps(asdict(rejected_seed), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        repo.set_group_match(group_id, 101, MATCH_STATUS_CONFIRMED, 0.95)
        match = repo.get_group_match(group_id)
        bulk = repo.get_group_matches([group_id, group_id + 1, group_id])

        assert match is not None
        assert match.tmdb_id == 101
        assert bulk[group_id].match_status == MATCH_STATUS_CONFIRMED

        repo.set_group_match(group_id, 202, MATCH_STATUS_REJECTED, 0.1)
        rejected = repo.get_group_match(group_id)
        assert rejected is not None
        assert rejected.match_status == MATCH_STATUS_REJECTED

        repo.invalidate_group_match(group_id)
        assert repo.get_group_match(group_id) is None
    finally:
        conn.close()


def test_title_match_repository_series_bulk_lookup_and_poster_state_changes(tmp_path: Path) -> None:
    conn = create_connection(tmp_path / "tmdb.db")
    repo = SqliteTitleMatchRepository(conn, threading.Lock())
    try:
        candidate = _candidate(10)
        repo.upsert_series(
            candidate,
            raw_json=json.dumps(asdict(candidate), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        repo.save_poster_asset(
            10,
            "poster",
            "/poster.jpg",
            local_path=str(tmp_path / "missing.jpg"),
            status="ready",
            verified_at="2026-01-01T00:00:00Z",
        )

        changed = _candidate(10, name_ko="Frieren")
        changed = changed.__class__(**{**asdict(changed), "poster_path": "/poster-new.jpg"})
        repo.upsert_series(
            changed,
            raw_json=json.dumps(asdict(changed), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        conn.execute(
            "UPDATE tmdb_series SET raw_json = ?, expires_at = ? WHERE tmdb_id = ?",
            ("not json", "2999-01-01T00:00:00Z", 999),
        )
        conn.commit()

        assert repo.get_poster_local_path(10, "poster", "/poster.jpg") is None
        assert repo.get_series_candidates([10, 10, 999]) == {10: changed}
    finally:
        conn.close()


def test_title_match_repository_local_search_filters_invalid_and_expired_rows(
    tmp_path: Path,
) -> None:
    conn = create_connection(tmp_path / "tmdb.db")
    repo = SqliteTitleMatchRepository(conn, threading.Lock())
    try:
        exact = _candidate(1, "Frieren")
        partial = _candidate(2, "Frieren Beyond Journey")
        expired = _candidate(3, "Frieren")
        repo.upsert_series(
            exact,
            raw_json=json.dumps(asdict(exact), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        repo.upsert_series(
            partial,
            raw_json=json.dumps(asdict(partial), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        repo.upsert_series(
            expired,
            raw_json=json.dumps(asdict(expired), ensure_ascii=False),
            expires_at="2000-01-01T00:00:00Z",
        )
        conn.execute(
            """
            INSERT INTO tmdb_series (
                tmdb_id, name_ko, original_name, poster_path, raw_json, expires_at, created_at, updated_at
            ) VALUES (55, 'Frieren', 'Frieren', '/poster.jpg', '[]', '2999-01-01T00:00:00Z', ?, ?)
            """,
            ("2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
        )
        conn.commit()

        found = repo.find_series_candidates_by_title("Frieren", limit=5)

        assert found[0].tmdb_id == 1
        assert {candidate.tmdb_id for candidate in found} == {1, 2}
        assert repo.find_series_candidates_by_title("f", limit=5) == []
    finally:
        conn.close()
