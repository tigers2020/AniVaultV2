from __future__ import annotations

import threading
from pathlib import Path
from threading import Event
from typing import Any

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_library_index_repository import (
    SqliteLibraryIndexRepository,
)
from anivault.application.use_cases.scan_library import make_execute
from anivault.contracts.library_index import BulkMediaUpsertItem, BulkMediaUpsertResult
from anivault.contracts.scan import ScanInput
from anivault.domain.path_norm import normalize_path_key


class _FileRepo:
    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths

    def list_files(self, *args: Any, **kwargs: Any) -> list[Path]:
        del args, kwargs
        return self.paths


class _BulkOnlyLibraryIndex:
    def __init__(self) -> None:
        self.bulk_files: list[BulkMediaUpsertItem] = []
        self.mark_missing_seen: set[str] | None = None
        self.finished: dict[str, object] | None = None

    def upsert_root(self, root_path: str, *, display_name: str | None = None) -> int:
        del root_path, display_name
        return 10

    def begin_scan(self, root_id: int, scan_kind: str) -> int:
        del root_id, scan_kind
        return 20

    def finish_scan(self, session_id: int, **kwargs: object) -> None:
        self.finished = {"session_id": session_id, **kwargs}

    def upsert_media_file(self, **kwargs: object) -> tuple[bool, bool]:
        del kwargs
        raise AssertionError("scan use case should use bulk upsert")

    def upsert_media_files(
        self,
        root_id: int,
        session_id: int,
        files: list[BulkMediaUpsertItem],
    ) -> BulkMediaUpsertResult:
        del root_id, session_id
        self.bulk_files = files
        return BulkMediaUpsertResult(
            files_added=1,
            files_updated=1,
            seen_path_norms={"seen-a", "seen-b"},
        )

    def mark_missing_deleted(
        self,
        root_id: int,
        session_id: int,
        seen_path_norms: set[str],
    ) -> int:
        del root_id, session_id
        self.mark_missing_seen = seen_path_norms
        return 3


def test_scan_library_uses_bulk_index_result_for_missing_mark(tmp_path: Path) -> None:
    files = [tmp_path / "a.mkv", tmp_path / "b.srt"]
    for file in files:
        file.write_bytes(b"media")
    library_index = _BulkOnlyLibraryIndex()
    execute = make_execute(_FileRepo(files), library_index=library_index)  # type: ignore[arg-type]

    result = execute(ScanInput(path=str(tmp_path)), None, Event())

    assert result.index_root_id == 10
    assert [item.absolute_path for item in library_index.bulk_files] == [str(p) for p in files]
    assert [item.media_kind for item in library_index.bulk_files] == ["video", "subtitle"]
    assert library_index.mark_missing_seen == {"seen-a", "seen-b"}
    assert library_index.finished == {
        "session_id": 20,
        "status": "success",
        "files_seen": 2,
        "files_added": 1,
        "files_updated": 1,
        "files_removed": 3,
    }


def test_sqlite_bulk_upsert_counts_and_seen_paths(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    library_root.mkdir()
    first = library_root / "first.mkv"
    second = library_root / "second.mkv"
    root_level_no_ext = library_root / "README"
    dotted = library_root / "Season 1" / "show.name.E01.MKV"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    root_level_no_ext.write_bytes(b"readme")
    dotted.parent.mkdir()
    dotted.write_bytes(b"dotted")
    conn = create_connection(tmp_path / "anivault.db")
    repo = SqliteLibraryIndexRepository(conn, threading.Lock())
    root_id = repo.upsert_root(str(library_root))
    scan_id = repo.begin_scan(root_id, "full")

    try:
        initial = repo.upsert_media_files(
            root_id,
            scan_id,
            [
                BulkMediaUpsertItem(str(first), "video"),
                BulkMediaUpsertItem(str(second), "video"),
                BulkMediaUpsertItem(str(root_level_no_ext), "video"),
                BulkMediaUpsertItem(str(dotted), "video"),
            ],
        )

        assert initial.files_added == 4
        assert initial.files_updated == 0
        assert initial.seen_path_norms == {
            normalize_path_key(first),
            normalize_path_key(second),
            normalize_path_key(root_level_no_ext),
            normalize_path_key(dotted),
        }
        meta_rows = conn.execute(
            """
            SELECT relative_path, dir_norm, file_name, file_stem, extension
            FROM media_files
            WHERE root_id = ?
            """,
            (root_id,),
        ).fetchall()
        meta_by_relative = {
            str(row[0]): tuple(str(value) for value in row[1:]) for row in meta_rows
        }
        assert meta_by_relative["README"] == ("", "README", "README", "")
        assert meta_by_relative["Season 1/show.name.E01.MKV"] == (
            "Season 1",
            "show.name.E01.MKV",
            "show.name.E01",
            ".mkv",
        )

        third = library_root / "third.mkv"
        third.write_bytes(b"third")
        next_scan_id = repo.begin_scan(root_id, "full")
        updated = repo.upsert_media_files(
            root_id,
            next_scan_id,
            [
                BulkMediaUpsertItem(str(first), "video"),
                BulkMediaUpsertItem(str(third), "video"),
            ],
        )
        removed = repo.mark_missing_deleted(root_id, next_scan_id, updated.seen_path_norms)

        assert updated.files_added == 1
        assert updated.files_updated == 1
        assert removed == 3
        records = repo.list_media_by_root(root_id, include_deleted=True)
        deleted_by_path = {record.path_norm: record.is_deleted for record in records}
        assert deleted_by_path[normalize_path_key(first)] is False
        assert deleted_by_path[normalize_path_key(second)] is True
        assert deleted_by_path[normalize_path_key(root_level_no_ext)] is True
        assert deleted_by_path[normalize_path_key(dotted)] is True
        assert deleted_by_path[normalize_path_key(third)] is False
        resolved = repo.resolve_media_for_parse(
            root_id,
            [
                str(first),
                str(first),
                str(second),
                str(third).replace("\\", "/"),
                str(tmp_path / "outside.mkv"),
            ],
        )
        assert resolved[0] is not None
        assert resolved[1] is not None
        assert resolved[0].id == resolved[1].id
        assert resolved[2] is None
        assert resolved[3] is not None
        assert resolved[4] is None
    finally:
        conn.close()
