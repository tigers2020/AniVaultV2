"""Integration: match use case with real SQLite repos and fake TMDB (no API)."""

from __future__ import annotations

from pathlib import Path
from threading import Event, Lock

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_parse_cache_repository import (
    SqliteParseCacheRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_title_group_repository import (
    SqliteTitleGroupRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_title_match_repository import (
    SqliteTitleMatchRepository,
)
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.sync_title_groups import (
    make_execute as make_sync_title_groups_execute,
)
from anivault.constants.gui.components import PIPELINE_ROW_STATUS_TMDB_MATCHED
from anivault.contracts.library_index import BulkMediaUpsertItem
from anivault.contracts.pipeline import MatchInput, PipelineRow
from anivault.domain.media.extensions import classify_media_kind
from anivault.domain.models import ParsedInfo
from anivault.domain.models.parsed_info_serde import parsed_info_to_compact_json
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parse_signature import compute_parse_input_signature
from anivault.domain.parsing.parser_version import PARSER_VERSION
from anivault.domain.path_norm import normalize_path_key
from tests.integration.fake_metadata_provider import FakeMetadataProvider


def _touch_mkv(parent: Path, name: str) -> Path:
    path = parent / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    return path


def _upsert_parse_ok(
    parse_cache: SqliteParseCacheRepository,
    media_file_id: int,
    path_norm: str,
    size_bytes: int,
    mtime_ns: int,
    parsed: ParsedInfo,
) -> None:
    signature = compute_parse_input_signature(path_norm, size_bytes, mtime_ns)
    parse_cache.upsert_parse_ok(
        media_file_id=media_file_id,
        parser_version=PARSER_VERSION,
        parse_input_signature=signature,
        parsed=parsed,
        dto_json=parsed_info_to_compact_json(parsed),
        parsed_title=parsed.title,
        parsed_title_normalized=normalize_title_for_parse_cache(parsed.title),
        parsed_year=int(parsed.year),
        season_number=int(parsed.season),
        episode_start=int(parsed.episode),
        episode_end=None,
        episode_count=None,
        confidence=None,
    )


def test_match_persists_series_and_group_match_with_sqlite(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    p1 = _touch_mkv(library_root / "ShowA", "Episode 01 1080p.mkv")
    p2 = _touch_mkv(library_root / "ShowA", "Episode 02 1080p.mkv")

    parsed = ParsedInfo(
        title="IntegrationSeries",
        parse_group="IntegrationSeries",
        year="2024",
        season="1",
        episode="1",
        resolution="FHD",
    )
    parsed2 = ParsedInfo(
        title="IntegrationSeries",
        parse_group="IntegrationSeries",
        year="2024",
        season="1",
        episode="2",
        resolution="FHD",
    )

    db_path = tmp_path / "anivault.db"
    conn = create_connection(db_path)
    lock = Lock()
    try:
        library_index = SqliteLibraryIndexRepository(conn, lock)
        parse_cache = SqliteParseCacheRepository(conn, lock)
        title_groups = SqliteTitleGroupRepository(conn, lock)
        title_match = SqliteTitleMatchRepository(conn, lock)

        root_id = library_index.upsert_root(str(library_root.resolve()))
        scan_id = library_index.begin_scan(root_id, "integration")
        library_index.upsert_media_files(
            root_id,
            scan_id,
            [
                BulkMediaUpsertItem(str(p1.resolve()), classify_media_kind(p1)),
                BulkMediaUpsertItem(str(p2.resolve()), classify_media_kind(p2)),
            ],
        )
        resolved = library_index.resolve_media_for_parse(
            root_id,
            [str(p1.resolve()), str(p2.resolve())],
        )
        assert len(resolved) == 2
        for meta, pinfo in zip(resolved, (parsed, parsed2), strict=True):
            assert meta is not None
            _upsert_parse_ok(
                parse_cache,
                meta.id,
                meta.path_norm,
                meta.size_bytes,
                meta.mtime_ns,
                pinfo,
            )
        library_index.finish_scan(
            scan_id,
            status="success",
            files_seen=2,
            files_added=2,
            files_updated=0,
            files_removed=0,
        )

        make_sync_title_groups_execute(title_groups)(root_id)
        rep_norm = normalize_path_key(str(p1.resolve()))
        group_id = title_groups.get_group_id_for_path_norm(root_id, rep_norm)
        assert group_id is not None

        rows = (
            PipelineRow(
                original_file=str(p1.resolve()),
                parsed_title=parsed.title,
                parse_group=parsed.parse_group,
                tmdb_korean_title_group="",
                tmdb_series_id="",
                tmdb_poster_path="",
                tmdb_backdrop_path="",
                year="2024",
                season="1",
                resolution="FHD",
                status="parsed",
                poster_url="",
                backdrop_url="",
                target_path="",
                episode=parsed.episode,
            ),
            PipelineRow(
                original_file=str(p2.resolve()),
                parsed_title=parsed2.title,
                parse_group=parsed2.parse_group,
                tmdb_korean_title_group="",
                tmdb_series_id="",
                tmdb_poster_path="",
                tmdb_backdrop_path="",
                year="2024",
                season="1",
                resolution="FHD",
                status="parsed",
                poster_url="",
                backdrop_url="",
                target_path="",
                episode=parsed2.episode,
            ),
        )

        match_execute = make_match_execute(
            FakeMetadataProvider(),
            title_match=title_match,
            title_groups=title_groups,
        )
        result = match_execute(MatchInput(files=rows, index_root_id=root_id), None, Event())

        assert len(result.files) == 2
        for row in result.files:
            assert row.tmdb_series_id == "424242"
            assert row.status == PIPELINE_ROW_STATUS_TMDB_MATCHED

        gm = title_match.get_group_match(group_id)
        assert gm is not None
        assert int(gm.tmdb_id) == 424242
        assert gm.match_status == "auto_matched"

        cached = title_match.get_series_candidate(424242)
        assert cached is not None
        assert cached.original_name
    finally:
        conn.close()
