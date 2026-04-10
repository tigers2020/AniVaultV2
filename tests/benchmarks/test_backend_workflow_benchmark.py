from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from dataclasses import asdict
from pathlib import Path
from threading import Event, Lock
from typing import Protocol, TypeVar

import pytest
from _helpers import SAMPLE_SIZES, load_filename_samples, synthetic_media_paths

from anivault.adapters.operation_log.fs_operation_log import FsOperationLogRepository
from anivault.adapters.parser.title_parser import AnitopyTitleParser
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
from anivault.application.use_cases.apply_plan import make_apply_execute
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
from anivault.application.use_cases.plan_moves import make_execute as make_plan_execute
from anivault.application.use_cases.scan_library import make_execute as make_scan_execute
from anivault.application.use_cases.sync_title_groups import make_execute as make_sync_execute
from anivault.contracts.library_index import BulkMediaUpsertItem
from anivault.contracts.parse import ParseInput
from anivault.contracts.pipeline import MatchInput, PipelineRow
from anivault.contracts.planning import ApplyInput, PlanInput
from anivault.contracts.scan import ScanInput
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.media.extensions import classify_media_kind
from anivault.domain.models import ParsedInfo
from anivault.domain.models.parsed_info_serde import parsed_info_to_compact_json
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parse_signature import compute_parse_input_signature
from anivault.domain.parsing.parser_version import PARSER_VERSION

T = TypeVar("T")


class BenchmarkCallable(Protocol):
    def __call__(self, target: Callable[[], T], *args: object, **kwargs: object) -> T: ...


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_anitopy_title_parser_timing(benchmark: BenchmarkCallable, sample_size: int) -> None:
    filenames = load_filename_samples(sample_size)
    parser = AnitopyTitleParser()

    parsed = benchmark(lambda: [parser.parse(filename) for filename in filenames])

    assert len(parsed) == sample_size


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_parse_titles_use_case_timing(benchmark: BenchmarkCallable, sample_size: int) -> None:
    filenames = load_filename_samples(sample_size)
    execute = make_parse_execute(AnitopyTitleParser())

    result = benchmark(lambda: execute(ParseInput(paths=filenames), None, Event()))

    assert len(result.parsed) == sample_size


class _StaticFileRepository:
    def __init__(self, paths: Sequence[Path]) -> None:
        self.paths = list(paths)

    def list_files(
        self,
        directory: Path,
        *,
        extensions: tuple[str, ...] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[int, str | None], None] | None = None,
        sort: bool = True,
    ) -> list[Path]:
        del directory, extensions, recursive, progress_callback, sort
        return self.paths

    def move(self, source: Path, destination: Path) -> None:
        del source, destination

    def copy(self, source: Path, destination: Path) -> None:
        del source, destination

    def prune_empty_dirs_under(self, root: Path) -> None:
        del root


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_scan_library_use_case_timing(
    benchmark: BenchmarkCallable,
    tmp_path: Path,
    sample_size: int,
) -> None:
    paths = synthetic_media_paths(tmp_path / "library", sample_size)
    execute = make_scan_execute(_StaticFileRepository(paths))

    result = benchmark(
        lambda: execute(ScanInput(path=str(tmp_path), sort_paths=False), None, Event())
    )

    assert len(result.paths) == sample_size
    assert len(result.resolutions) == sample_size


def _touch_media_files(root: Path, size: int) -> list[Path]:
    paths = synthetic_media_paths(root, size)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"media")
    return paths


def _parsed_info_for_index(index: int) -> ParsedInfo:
    title = f"Series {index // 12:04d}"
    return ParsedInfo(
        title=title,
        parse_group=title,
        year="2024",
        season="1",
        episode=str(index % 12 + 1),
        resolution="FHD",
    )


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


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_sqlite_index_and_parse_cache_timing(
    benchmark: BenchmarkCallable,
    tmp_path: Path,
    sample_size: int,
) -> None:
    library_root = tmp_path / "library"
    paths = _touch_media_files(library_root, sample_size)
    conn = create_connection(tmp_path / "index-cache.db")
    lock = Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    parse_cache = SqliteParseCacheRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))

    def index_and_cache() -> int:
        scan_id = library_index.begin_scan(root_id, "benchmark")
        library_index.upsert_media_files(
            root_id,
            scan_id,
            [BulkMediaUpsertItem(str(path), classify_media_kind(path)) for path in paths],
        )
        resolved = library_index.resolve_media_for_parse(root_id, [str(path) for path in paths])
        cached = 0
        for index, meta in enumerate(resolved):
            assert meta is not None
            parsed = _parsed_info_for_index(index)
            _upsert_parse_ok(
                parse_cache,
                meta.id,
                meta.path_norm,
                meta.size_bytes,
                meta.mtime_ns,
                parsed,
            )
            signature = compute_parse_input_signature(
                meta.path_norm, meta.size_bytes, meta.mtime_ns
            )
            if parse_cache.get_valid_parse(meta.id, signature) is not None:
                cached += 1
        library_index.finish_scan(
            scan_id,
            status="success",
            files_seen=len(paths),
            files_added=0,
            files_updated=len(paths),
            files_removed=0,
        )
        return cached

    try:
        cached_count = benchmark(index_and_cache)
    finally:
        conn.close()

    assert cached_count == sample_size


def _seed_sqlite_parse_cache(
    db_path: Path,
    library_root: Path,
    size: int,
) -> tuple[int, list[Path]]:
    paths = _touch_media_files(library_root, size)
    conn = create_connection(db_path)
    lock = Lock()
    library_index = SqliteLibraryIndexRepository(conn, lock)
    parse_cache = SqliteParseCacheRepository(conn, lock)
    root_id = library_index.upsert_root(str(library_root))
    scan_id = library_index.begin_scan(root_id, "benchmark")
    library_index.upsert_media_files(
        root_id,
        scan_id,
        [BulkMediaUpsertItem(str(path), classify_media_kind(path)) for path in paths],
    )
    resolved = library_index.resolve_media_for_parse(root_id, [str(path) for path in paths])
    for index, meta in enumerate(resolved):
        assert meta is not None
        _upsert_parse_ok(
            parse_cache,
            meta.id,
            meta.path_norm,
            meta.size_bytes,
            meta.mtime_ns,
            _parsed_info_for_index(index),
        )
    library_index.finish_scan(
        scan_id,
        status="success",
        files_seen=len(paths),
        files_added=len(paths),
        files_updated=0,
        files_removed=0,
    )
    conn.close()
    return root_id, paths


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_sync_title_groups_timing(
    benchmark: BenchmarkCallable,
    tmp_path: Path,
    sample_size: int,
) -> None:
    root_id, _paths = _seed_sqlite_parse_cache(
        tmp_path / "groups.db",
        tmp_path / "library",
        sample_size,
    )
    conn = create_connection(tmp_path / "groups.db")
    lock = Lock()
    title_groups = SqliteTitleGroupRepository(conn, lock)
    execute = make_sync_execute(title_groups)

    try:
        benchmark(lambda: execute(root_id))
        groups = title_groups.list_title_groups_for_root(root_id)
    finally:
        conn.close()

    assert groups


class _FakeMetadataProvider:
    def search_series(
        self,
        query: str,
        *,
        year: int | None = None,
    ) -> Sequence[TmdbSeriesCandidate]:
        del year
        tmdb_id = abs(hash(query)) % 1_000_000 + 1
        return (
            TmdbSeriesCandidate(
                tmdb_id=tmdb_id,
                name_ko=f"{query} KO",
                original_name=query,
                first_air_date="2024-01-01",
                original_language="ja",
                overview="",
                poster_path=f"/{tmdb_id}.jpg",
                backdrop_path=f"/{tmdb_id}-backdrop.jpg",
                popularity=10.0,
            ),
        )


def _match_rows(paths: Sequence[str]) -> tuple[PipelineRow, ...]:
    return tuple(
        PipelineRow(
            original_file=path,
            parsed_title=f"Series {index // 12:04d}",
            parse_group=f"Series {index // 12:04d}",
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
            episode=str(index % 12 + 1),
        )
        for index, path in enumerate(paths)
    )


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_match_series_use_case_timing(
    benchmark: BenchmarkCallable,
    sample_size: int,
) -> None:
    filenames = load_filename_samples(sample_size)
    execute = make_match_execute(_FakeMetadataProvider())

    result = benchmark(lambda: execute(MatchInput(files=_match_rows(filenames)), None, Event()))

    assert len(result.files) == sample_size
    assert result.groups


def _matched_rows(paths: Sequence[str]) -> tuple[PipelineRow, ...]:
    return tuple(
        PipelineRow(
            original_file=path,
            parsed_title=f"Series {index // 12:04d}",
            parse_group=f"Series {index // 12:04d}",
            tmdb_korean_title_group=f"Series {index // 12:04d} KO",
            tmdb_series_id=str(index // 12 + 1),
            tmdb_poster_path="",
            tmdb_backdrop_path="",
            year="2024",
            season="1",
            resolution="FHD",
            status="TMDB matched",
            poster_url="",
            backdrop_url="",
            target_path="",
            episode=str(index % 12 + 1),
        )
        for index, path in enumerate(paths)
    )


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_plan_moves_use_case_timing(benchmark: BenchmarkCallable, sample_size: int) -> None:
    filenames = load_filename_samples(sample_size)
    rows = _matched_rows(filenames)
    execute = make_plan_execute()

    result = benchmark(
        lambda: execute(
            PlanInput(
                files=rows,
                path_template="{korean_title_group}/Season {season}/{original_file}",
                target_root="F:/AniVault/Organized",
                unknown_resolution="Unknown Resolution",
                unknown_group_folder="Unknown Title",
                include_companion_subtitles=False,
            ),
            None,
            Event(),
        )
    )

    assert result.error is None
    assert len(result.moves) == sample_size


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_apply_plan_dry_run_timing(
    benchmark: BenchmarkCallable,
    tmp_path: Path,
    sample_size: int,
) -> None:
    rows = _matched_rows(load_filename_samples(sample_size))
    plan = make_plan_execute()(
        PlanInput(
            files=rows,
            path_template="{korean_title_group}/Season {season}/{original_file}",
            target_root=str(tmp_path / "organized"),
            unknown_resolution="Unknown Resolution",
            unknown_group_folder="Unknown Title",
            include_companion_subtitles=False,
        ),
        None,
        Event(),
    )
    execute = make_apply_execute(_StaticFileRepository(()), FsOperationLogRepository)

    result = benchmark(
        lambda: execute(
            ApplyInput(
                operations=plan.moves,
                dry_run=True,
                log_root=str(tmp_path / "logs"),
                source_root=None,
            ),
            None,
            Event(),
        )
    )

    assert result.error is None
    assert result.log_path is not None


@pytest.mark.benchmark
@pytest.mark.parametrize("sample_size", SAMPLE_SIZES)
def test_cached_hydrate_with_sqlite_timing(
    benchmark: BenchmarkCallable,
    tmp_path: Path,
    sample_size: int,
) -> None:
    root_id, paths = _seed_sqlite_parse_cache(
        tmp_path / "hydrate.db",
        tmp_path / "library",
        sample_size,
    )
    conn = create_connection(tmp_path / "hydrate.db")
    lock = Lock()
    title_groups = SqliteTitleGroupRepository(conn, lock)
    title_match = SqliteTitleMatchRepository(conn, lock)
    make_sync_execute(title_groups)(root_id)
    groups = title_groups.list_title_groups_for_root(root_id)
    for group in groups:
        candidate = TmdbSeriesCandidate(
            tmdb_id=group.id + 10_000,
            name_ko=f"{group.canonical_title} KO",
            original_name=group.canonical_title or group.group_key,
            first_air_date="2024-01-01",
            original_language="ja",
            overview="",
            poster_path=f"/{group.id}.jpg",
            backdrop_path="",
            popularity=10.0,
        )
        title_match.upsert_series(
            candidate,
            raw_json=json.dumps(asdict(candidate), ensure_ascii=False, separators=(",", ":")),
            expires_at="2999-01-01T00:00:00Z",
        )
        title_match.set_group_match(group.id, candidate.tmdb_id, "confirmed", None)

    from anivault.application.use_cases.hydrate_cached_tmdb_matches import make_execute

    execute = make_execute(title_match=title_match, title_groups=title_groups)
    rows = _match_rows([str(path) for path in paths])

    try:
        result = benchmark(lambda: execute(MatchInput(files=rows, index_root_id=root_id)))
    finally:
        conn.close()

    assert len(result.files) == sample_size
    assert any(row.tmdb_series_id for row in result.files)
