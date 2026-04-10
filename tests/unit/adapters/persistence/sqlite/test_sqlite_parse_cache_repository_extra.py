from __future__ import annotations

import threading
from pathlib import Path

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.adapters.persistence.sqlite.sqlite_parse_cache_repository import (
    SqliteParseCacheRepository,
)
from anivault.contracts.library_index import BulkMediaUpsertItem, IndexedMediaForParse
from anivault.contracts.parse_cache import ParseCacheErrorWrite
from anivault.domain.models import ParsedInfo
from anivault.domain.models.parsed_info_serde import parsed_info_to_compact_json
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parser_version import PARSER_VERSION


def _ok_write(media_file_id: int, signature: str, parsed: ParsedInfo):
    from anivault.contracts.parse_cache import ParseCacheOkWrite

    return ParseCacheOkWrite(
        media_file_id=media_file_id,
        parser_version=PARSER_VERSION,
        parse_input_signature=signature,
        parsed=parsed,
        dto_json=parsed_info_to_compact_json(parsed),
        parsed_title=parsed.title,
        parsed_title_normalized=normalize_title_for_parse_cache(parsed.title),
        parsed_year=int(parsed.year),
        season_number=int(parsed.season),
        episode_start=parsed.episode_numbers[0],
        episode_end=parsed.episode_numbers[-1],
        episode_count=len(parsed.episode_numbers),
        confidence=None,
    )


def _seed_media(tmp_path: Path, count: int) -> tuple[object, list[IndexedMediaForParse]]:
    library_root = tmp_path / "library"
    library_root.mkdir()
    paths: list[Path] = []
    for index in range(count):
        path = library_root / f"show-{index}.mkv"
        path.write_bytes(b"media")
        paths.append(path)
    conn = create_connection(tmp_path / "parse-cache-extra.db")
    lock = threading.Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))
    scan_id = library_index.begin_scan(root_id, "test")
    library_index.upsert_media_files(
        root_id,
        scan_id,
        [BulkMediaUpsertItem(str(path), "video") for path in paths],
    )
    resolved = library_index.resolve_media_for_parse(root_id, [str(path) for path in paths])
    assert all(meta is not None for meta in resolved)
    return conn, [meta for meta in resolved if meta is not None]


def test_parse_cache_single_upserts_and_resolution_paths(tmp_path: Path) -> None:
    conn, media = _seed_media(tmp_path, 2)
    repo = SqliteParseCacheRepository(conn, threading.Lock())
    parsed = ParsedInfo(
        title="Show",
        parse_group="Show",
        year="2024",
        season="1",
        episode="01",
        episode_numbers=[1],
        resolution="1080p",
    )
    try:
        repo.upsert_parse_ok(
            media_file_id=media[0].id,
            parser_version=PARSER_VERSION,
            parse_input_signature="sig-ok",
            parsed=parsed,
            dto_json='{"title":"Show"}',
            parsed_title="Show",
            parsed_title_normalized="show",
            parsed_year=2024,
            season_number=1,
            episode_start=1,
            episode_end=1,
            episode_count=1,
            confidence=0.8,
        )
        repo.upsert_parse_error(
            media_file_id=media[1].id,
            parser_version=PARSER_VERSION,
            parse_input_signature="sig-err",
            error_code="ValueError",
            error_message="bad parse",
        )
        repo.upsert_resolution(
            media_file_id=media[0].id,
            signature="res-sig",
            value="1080p",
            source="ffprobe",
        )

        assert repo.get_valid_parse(media[0].id, "sig-ok") is not None
        assert repo.get_valid_parse(media[1].id, "sig-err") is None
        assert repo.get_valid_resolution(media[0].id, "res-sig") == "1080p"
        assert repo.get_valid_resolution(media[0].id, "wrong") is None
        assert repo.get_valid_resolution(media[1].id, "res-sig") is None
    finally:
        conn.close()


def test_parse_cache_resolution_batch_commits_and_rolls_back(tmp_path: Path) -> None:
    conn, media = _seed_media(tmp_path, 1)
    repo = SqliteParseCacheRepository(conn, threading.Lock())
    try:
        with repo.resolution_write_batch():
            repo.upsert_resolution(
                media_file_id=media[0].id,
                signature="sig-1",
                value="720p",
                source="filename",
            )
            repo.upsert_resolution(
                media_file_id=media[0].id,
                signature="sig-2",
                value="1080p",
                source="ffprobe",
            )
        assert repo.get_valid_resolution(media[0].id, "sig-2") == "1080p"

        try:
            with repo.resolution_write_batch():
                repo.upsert_resolution(
                    media_file_id=media[0].id,
                    signature="sig-3",
                    value="480p",
                    source="filename",
                )
                raise RuntimeError("boom")
        except RuntimeError:
            pass

        assert repo.get_valid_resolution(media[0].id, "sig-3") is None
    finally:
        conn.close()


def test_parse_cache_bulk_methods_ignore_empty_inputs(tmp_path: Path) -> None:
    conn, media = _seed_media(tmp_path, 1)
    repo = SqliteParseCacheRepository(conn, threading.Lock())
    parsed = ParsedInfo(
        title="Show",
        parse_group="Show",
        year="2024",
        season="1",
        episode="01",
        episode_numbers=[1],
        resolution="1080p",
    )
    try:
        repo.upsert_parse_ok_many([])
        repo.upsert_parse_error_many([])
        repo.upsert_resolution(media_file_id=media[0].id, signature="sig", value="   ", source="")

        repo.upsert_parse_ok_many([_ok_write(media[0].id, "sig", parsed)])
        repo.upsert_parse_error_many(
            [
                ParseCacheErrorWrite(
                    media_file_id=media[0].id,
                    parser_version="v2",
                    parse_input_signature="sig-error",
                    error_code=None,
                    error_message=None,
                )
            ]
        )

        assert repo.get_valid_parse(media[0].id, "sig") is None
    finally:
        conn.close()
