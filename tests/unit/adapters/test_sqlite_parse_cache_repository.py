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
from anivault.application.dto.library_index import BulkMediaUpsertItem, IndexedMediaForParse
from anivault.application.dto.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.application.dto.parse_serde import parsed_info_to_compact_json
from anivault.domain.models import ParsedInfo
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parser_version import PARSER_VERSION


def _parsed(title: str) -> ParsedInfo:
    return ParsedInfo(
        title=title,
        parse_group=title,
        year="2025",
        season="1",
        episode="01",
        resolution="1080p",
    )


def _ok_write(media_file_id: int, signature: str, parsed: ParsedInfo) -> ParseCacheOkWrite:
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
        episode_start=int(parsed.episode),
        episode_end=None,
        episode_count=None,
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
    conn = create_connection(tmp_path / "parse-cache.db")
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


def test_sqlite_parse_cache_bulk_write_and_read_filters_invalid_rows(tmp_path: Path) -> None:
    conn, media = _seed_media(tmp_path, 4)
    cache = SqliteParseCacheRepository(conn, threading.Lock())
    first = _parsed("First")
    second = _parsed("Second")

    try:
        cache.upsert_parse_ok_many(
            [
                _ok_write(media[0].id, "sig-1", first),
                _ok_write(media[1].id, "sig-2", second),
            ]
        )
        cache.upsert_parse_error_many(
            [
                ParseCacheErrorWrite(
                    media_file_id=media[2].id,
                    parser_version=PARSER_VERSION,
                    parse_input_signature="sig-3",
                    error_code="ValueError",
                    error_message="bad",
                )
            ]
        )
        cache.upsert_parse_ok_many([_ok_write(media[3].id, "sig-4", _parsed("Broken"))])
        conn.execute(
            "UPDATE parse_cache SET dto_json = ? WHERE media_file_id = ?",
            ("not json", media[3].id),
        )
        conn.commit()

        hits = cache.get_valid_parses(
            [
                ParseCacheLookup(media[0].id, "sig-1"),
                ParseCacheLookup(media[1].id, "wrong"),
                ParseCacheLookup(media[2].id, "sig-3"),
                ParseCacheLookup(media[3].id, "sig-4"),
            ]
        )

        assert hits == {media[0].id: first}
        assert cache.get_valid_parse(media[0].id, "sig-1") == first
        assert cache.get_valid_parse(media[2].id, "sig-3") is None
    finally:
        conn.close()
