from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from threading import Lock

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
from anivault.application.dto.title_match import GroupTmdbMatchRecord
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.domain.media.extensions import classify_media_kind


def _seed_grouped_media(
    tmp_path: Path,
) -> tuple[
    SqliteTitleGroupRepository,
    SqliteTitleMatchRepository,
    SqliteLibraryIndexRepository,
    int,
    int,
    list[object],
]:
    db_path = tmp_path / "title-cache.db"
    library_root = tmp_path / "library"
    paths = [
        library_root / "show-01.mkv",
        library_root / "show-02.mkv",
    ]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"media")
    conn = create_connection(db_path)
    lock = Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    title_groups = SqliteTitleGroupRepository(conn, lock)
    title_match = SqliteTitleMatchRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))
    scan_id = library_index.begin_scan(root_id, "test")
    library_index.upsert_media_files(
        root_id,
        scan_id,
        [BulkMediaUpsertItem(str(path), classify_media_kind(path)) for path in paths],
    )
    resolved = library_index.resolve_media_for_parse(root_id, [str(path) for path in paths])
    assert resolved[0] is not None
    assert resolved[1] is not None
    with lock:
        cur = conn.execute(
            """
            INSERT INTO title_groups (
                root_id, group_key, group_type, group_confidence,
                canonical_title, canonical_title_normalized,
                tmdb_series_id, member_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                root_id,
                "Parsed",
                "parsed_title_norm",
                None,
                "Parsed",
                "parsed",
                None,
                1,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        group_id = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO title_group_members (group_id, media_file_id, member_role, score)
            VALUES (?, ?, ?, ?)
            """,
            (group_id, resolved[0].id, "primary_video", None),
        )
        conn.commit()
    return title_groups, title_match, library_index, root_id, group_id, [resolved[0], resolved[1]]


def test_sqlite_title_group_bulk_lookup_returns_matching_path_norms(tmp_path: Path) -> None:
    title_groups, title_match, library_index, root_id, group_id, resolved = _seed_grouped_media(
        tmp_path
    )
    del title_match, library_index

    result = title_groups.get_group_ids_for_path_norms(
        root_id,
        [resolved[0].path_norm, resolved[1].path_norm, resolved[0].path_norm, ""],
    )

    assert result == {resolved[0].path_norm: group_id}


def test_sqlite_title_match_bulk_lookup_filters_expired_and_invalid_candidates(
    tmp_path: Path,
) -> None:
    title_groups, title_match, library_index, root_id, group_id, resolved = _seed_grouped_media(
        tmp_path
    )
    del library_index, resolved
    valid = TmdbSeriesCandidateDTO(
        tmdb_id=1001,
        name_ko="Valid",
        original_name="Valid Original",
        first_air_date="2024-01-01",
        original_language="ja",
        overview="",
        poster_path="/valid.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    expired = TmdbSeriesCandidateDTO(
        tmdb_id=1002,
        name_ko="Expired",
        original_name="Expired Original",
        first_air_date="2024-01-01",
        original_language="ja",
        overview="",
        poster_path="/expired.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    invalid = TmdbSeriesCandidateDTO(
        tmdb_id=1003,
        name_ko="Invalid",
        original_name="Invalid Original",
        first_air_date="2024-01-01",
        original_language="ja",
        overview="",
        poster_path="/invalid.jpg",
        backdrop_path="",
        popularity=1.0,
    )
    title_match.upsert_series(
        valid,
        raw_json=json.dumps(asdict(valid), ensure_ascii=False, separators=(",", ":")),
        expires_at="2999-01-01T00:00:00Z",
    )
    title_match.upsert_series(
        expired,
        raw_json=json.dumps(asdict(expired), ensure_ascii=False, separators=(",", ":")),
        expires_at="2000-01-01T00:00:00Z",
    )
    title_match.upsert_series(
        invalid,
        raw_json=json.dumps(asdict(invalid), ensure_ascii=False, separators=(",", ":")),
        expires_at="2999-01-01T00:00:00Z",
    )
    title_match.set_group_match(group_id, valid.tmdb_id, "confirmed", None)
    with title_match._lock:  # noqa: SLF001
        cur = title_match._conn.execute(  # noqa: SLF001
            """
            INSERT INTO title_groups (
                root_id, group_key, group_type, group_confidence,
                canonical_title, canonical_title_normalized,
                tmdb_series_id, member_count, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                root_id,
                "Rejected",
                "parsed_title_norm",
                None,
                "Rejected",
                "rejected",
                None,
                0,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        rejected_group_id = int(cur.lastrowid)
        title_match._conn.execute(  # noqa: SLF001
            "UPDATE tmdb_series SET raw_json = ? WHERE tmdb_id = ?",
            ("not json", invalid.tmdb_id),
        )
        title_match._conn.commit()  # noqa: SLF001
        title_match._conn.execute(  # noqa: SLF001
            """
            INSERT INTO group_tmdb_matches (
                group_id, tmdb_id, match_status, match_score, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(group_id) DO UPDATE SET
                tmdb_id = excluded.tmdb_id,
                match_status = excluded.match_status,
                match_score = excluded.match_score,
                updated_at = excluded.updated_at
            """,
            (
                rejected_group_id,
                expired.tmdb_id,
                "rejected",
                None,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        title_match._conn.commit()  # noqa: SLF001

    matches = title_match.get_group_matches([group_id, rejected_group_id, rejected_group_id + 1])
    candidates = title_match.get_series_candidates(
        [valid.tmdb_id, expired.tmdb_id, invalid.tmdb_id]
    )

    assert matches == {
        group_id: GroupTmdbMatchRecord(
            group_id=group_id,
            tmdb_id=valid.tmdb_id,
            match_status="confirmed",
            match_score=None,
        ),
        rejected_group_id: GroupTmdbMatchRecord(
            group_id=rejected_group_id,
            tmdb_id=expired.tmdb_id,
            match_status="rejected",
            match_score=None,
        ),
    }
    assert candidates == {valid.tmdb_id: valid}
