from __future__ import annotations

import threading
from pathlib import Path

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_title_group_repository import (
    SqliteTitleGroupRepository,
)
from anivault.application.dto.library_index import BulkMediaUpsertItem
from anivault.application.dto.title_groups import TitleGroupMemberSync, TitleGroupSyncBundle
from anivault.domain.media.extensions import classify_media_kind


def _seed_repo(tmp_path: Path) -> tuple[object, SqliteTitleGroupRepository, int, list[object]]:
    db_path = tmp_path / "groups.db"
    library_root = tmp_path / "library"
    paths = [library_root / "show-01.mkv", library_root / "show-02.mkv"]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"media")
    conn = create_connection(db_path)
    lock = threading.Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    repo = SqliteTitleGroupRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))
    scan_id = library_index.begin_scan(root_id, "test")
    library_index.upsert_media_files(
        root_id,
        scan_id,
        [BulkMediaUpsertItem(str(path), classify_media_kind(path)) for path in paths],
    )
    resolved = library_index.resolve_media_for_parse(root_id, [str(path) for path in paths])
    assert resolved[0] is not None and resolved[1] is not None
    with lock:
        conn.execute(
            """
            INSERT INTO parse_cache (
                media_file_id, parser_version, parse_input_signature, parse_status, dto_json,
                parsed_title, parsed_title_normalized, parsed_year,
                season_number, episode_start, episode_end, episode_count,
                confidence, error_code, error_message, created_at, updated_at
            ) VALUES (?, 'v1', ?, 'ok', '{}', ?, ?, 2024, 1, 1, NULL, NULL, NULL, NULL, NULL, ?, ?)
            """,
            (
                resolved[0].id,
                "sig-1",
                "Show",
                "show",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        conn.execute(
            """
            INSERT INTO parse_cache (
                media_file_id, parser_version, parse_input_signature, parse_status, dto_json,
                parsed_title, parsed_title_normalized, parsed_year,
                season_number, episode_start, episode_end, episode_count,
                confidence, error_code, error_message, created_at, updated_at
            ) VALUES (?, 'v1', ?, 'ok', '{}', ?, ?, 2025, 1, 2, NULL, NULL, NULL, NULL, NULL, ?, ?)
            """,
            (
                resolved[1].id,
                "sig-2",
                "Show 2",
                "show-2",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
        conn.commit()
    return conn, repo, root_id, [resolved[0], resolved[1]]


def test_sqlite_title_group_repository_replace_and_lookup(tmp_path: Path) -> None:
    conn, repo, root_id, resolved = _seed_repo(tmp_path)
    try:
        rows = repo.load_rows_for_grouping(root_id)
        repo.replace_root_title_groups(
            root_id,
            [
                TitleGroupSyncBundle(
                    group_key="Show",
                    group_type="parsed_title_norm",
                    canonical_title="Show",
                    canonical_title_normalized="show",
                    tmdb_series_id=None,
                    group_confidence=0.9,
                    members=(TitleGroupMemberSync(resolved[0].id, "primary_video", 0.9),),
                )
            ],
        )
        groups = repo.list_title_groups_for_root(root_id)
        group_id = repo.get_group_id(root_id, "Show")
        by_path = repo.get_group_id_for_path_norm(root_id, resolved[0].path_norm)

        assert len(rows) == 2
        assert len(groups) == 1
        assert group_id is not None
        assert by_path == group_id
        assert repo.get_group_id(root_id, "") is None
    finally:
        conn.close()


def test_sqlite_title_group_repository_replace_members_and_bulk_lookup(tmp_path: Path) -> None:
    conn, repo, root_id, resolved = _seed_repo(tmp_path)
    try:
        repo.replace_root_title_groups(
            root_id,
            [
                TitleGroupSyncBundle(
                    group_key="Show",
                    group_type="parsed_title_norm",
                    canonical_title="Show",
                    canonical_title_normalized="show",
                    tmdb_series_id=None,
                    group_confidence=None,
                    members=(TitleGroupMemberSync(resolved[0].id, "primary_video", 0.9),),
                )
            ],
        )
        group_id = repo.get_group_id(root_id, "Show")
        assert group_id is not None

        repo.replace_group_members(
            group_id,
            [
                TitleGroupMemberSync(resolved[0].id, "primary_video", 0.8),
                TitleGroupMemberSync(resolved[1].id, "other", 0.6),
            ],
        )

        found = repo.get_group_ids_for_path_norms(
            root_id,
            [resolved[0].path_norm, resolved[1].path_norm, resolved[0].path_norm, ""],
        )

        assert found == {resolved[0].path_norm: group_id, resolved[1].path_norm: group_id}
    finally:
        conn.close()
