"""Dependency wiring for GUI pages, use cases, and adapters."""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING

from anivault.adapters.fs import FsFileRepository
from anivault.adapters.media import FfprobeStreamResolution
from anivault.adapters.metadata.tmdb import (
    CachingMetadataProvider,
    TmdbApiClient,
    TmdbMetadataProvider,
)
from anivault.adapters.metadata.tmdb.poster_asset_sync import TmdbPosterAssetSync
from anivault.adapters.operation_log import FsOperationLogRepository
from anivault.adapters.parser import AnitopyTitleParser
from anivault.adapters.persistence.sqlite import (
    SqliteLibraryIndexRepository,
    SqliteOrganizePlanRepository,
    SqliteParseCacheRepository,
    SqliteTitleGroupRepository,
    SqliteTitleMatchRepository,
    SqliteTmdbSearchTvLibraryRepository,
    create_connection,
)
from anivault.adapters.persistence.sqlite.db_path import default_poster_cache_dir
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.operation_log_port import OperationLogRepository
from anivault.application.use_cases.apply_plan import make_apply_execute
from anivault.application.use_cases.fill_missing_cached_tmdb_matches import (
    make_execute as make_cached_tmdb_missing_fill_execute,
)
from anivault.application.use_cases.hydrate_cached_tmdb_matches import (
    make_execute as make_cached_tmdb_hydrate_execute,
)
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
from anivault.application.use_cases.persist_search_tv_library import (
    make_execute as make_persist_search_tv_library_execute,
)
from anivault.application.use_cases.plan_moves import make_execute as make_plan_execute
from anivault.application.use_cases.scan_library import make_execute as make_scan_execute
from anivault.application.use_cases.sync_title_groups import (
    make_execute as make_sync_title_groups_execute,
)
from anivault.bootstrap.env_file import read_tmdb_api_key
from anivault.constants.gui.settings import parse_ignore_tokens_from_loaded
from anivault.contracts.parse import ParseInput, ParseResult
from anivault.contracts.pipeline import MatchInput, MatchResult
from anivault.contracts.progress import ProgressEvent
from anivault.contracts.tmdb import TmdbSearchInput, TmdbSeriesCandidate
from anivault.domain.media.extensions import SUBTITLE_SCAN_EXTENSIONS
from anivault.domain.rules.tmdb_search_query import iter_strip_last_word_chain
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.pages import OrganizerPage, SettingsPage
from anivault.interfaces.gui.presenters import (
    OrganizerPresenter,
    OrganizerPresenterPorts,
    SettingsPresenter,
)
from anivault.interfaces.gui.settings_storage import load_all

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog


TmdbSearchExecute = Callable[
    [TmdbSearchInput, Callable[[ProgressEvent], None] | None, Event],
    tuple[TmdbSeriesCandidate, ...],
]


@dataclass(frozen=True)
class _SqliteRepositories:
    connection: sqlite3.Connection
    lock: threading.Lock
    library_index: SqliteLibraryIndexRepository
    organize_plan: SqliteOrganizePlanRepository
    parse_cache: SqliteParseCacheRepository
    title_groups: SqliteTitleGroupRepository
    title_match: SqliteTitleMatchRepository
    search_tv_library: SqliteTmdbSearchTvLibraryRepository


@dataclass(frozen=True)
class _OrganizerDependencies:
    file_repo: FsFileRepository
    resolution_probe: FfprobeStreamResolution
    repos: _SqliteRepositories


@dataclass(frozen=True)
class _TmdbRuntime:
    metadata: CachingMetadataProvider
    poster_sync: TmdbPosterAssetSync
    match_execute: Callable[
        [MatchInput, Callable[[ProgressEvent], None] | None, Event],
        MatchResult,
    ]
    tmdb_search_execute: TmdbSearchExecute
    cached_tmdb_missing_fill_execute: Callable[[MatchInput, object, Event], MatchResult]


class AniVaultAppContainer:
    """Application-scoped dependency container for shared GUI services."""

    def __init__(self) -> None:
        self._dependencies = _create_organizer_dependencies()
        self._tmdb_runtime = _create_tmdb_runtime(self._dependencies.repos)

    def create_organizer_page(
        self,
        pipeline_model: PipelineTableModel | None = None,
        progress_dialog: ProgressDialog | None = None,
    ) -> OrganizerPage:
        return _build_organizer_page(
            pipeline_model=pipeline_model,
            progress_dialog=progress_dialog,
            scan_extensions=None,
            include_companion_subtitles=True,
            dependencies=self._dependencies,
            tmdb_runtime=self._tmdb_runtime,
        )

    def create_subtitle_organizer_page(
        self,
        pipeline_model: PipelineTableModel | None = None,
        progress_dialog: ProgressDialog | None = None,
    ) -> OrganizerPage:
        return _build_organizer_page(
            pipeline_model=pipeline_model,
            progress_dialog=progress_dialog,
            scan_extensions=SUBTITLE_SCAN_EXTENSIONS,
            include_companion_subtitles=False,
            exclude_subtitles_with_paired_video=True,
            dependencies=self._dependencies,
            tmdb_runtime=self._tmdb_runtime,
        )

    def create_settings_page(self) -> SettingsPage:
        return create_settings_page()

    def close(self) -> None:
        with suppress(sqlite3.Error):
            self._dependencies.repos.connection.close()


def make_tmdb_search_execute(provider: MetadataProvider) -> TmdbSearchExecute:
    """Create a background-safe TMDB search execute function from a metadata provider."""

    def execute(
        input_dto: TmdbSearchInput,
        progress_callback: Callable[[ProgressEvent], None] | None,
        cancel_token: Event,
    ) -> tuple[TmdbSeriesCandidate, ...]:
        del progress_callback
        if cancel_token.is_set():
            return ()
        query = (input_dto.query or "").strip()
        if not query:
            return ()
        for attempt in iter_strip_last_word_chain(query):
            found = tuple(provider.search_series(attempt, year=input_dto.year))
            if found:
                return found
        return ()

    return execute


def create_organizer_page(
    pipeline_model: PipelineTableModel | None = None,
    progress_dialog: ProgressDialog | None = None,
) -> OrganizerPage:
    """Create the main video organizer page with use cases and adapters wired."""
    return _create_organizer_page(
        pipeline_model=pipeline_model,
        progress_dialog=progress_dialog,
        scan_extensions=None,
        include_companion_subtitles=True,
    )


def create_subtitle_organizer_page(
    pipeline_model: PipelineTableModel | None = None,
    progress_dialog: ProgressDialog | None = None,
) -> OrganizerPage:
    """Create the subtitle-only organizer page with shared wiring."""
    return _create_organizer_page(
        pipeline_model=pipeline_model,
        progress_dialog=progress_dialog,
        scan_extensions=SUBTITLE_SCAN_EXTENSIONS,
        include_companion_subtitles=False,
        exclude_subtitles_with_paired_video=True,
    )


def create_settings_page() -> SettingsPage:
    """Create the settings page with its presenter."""
    return SettingsPage(presenter=SettingsPresenter())


def _create_organizer_dependencies() -> _OrganizerDependencies:
    return _OrganizerDependencies(
        file_repo=FsFileRepository(),
        resolution_probe=FfprobeStreamResolution(),
        repos=_create_sqlite_repositories(),
    )


def _create_organizer_page(
    *,
    pipeline_model: PipelineTableModel | None,
    progress_dialog: ProgressDialog | None,
    scan_extensions: tuple[str, ...] | None,
    include_companion_subtitles: bool,
    exclude_subtitles_with_paired_video: bool = False,
) -> OrganizerPage:
    dependencies = _create_organizer_dependencies()
    tmdb_runtime = _create_tmdb_runtime(dependencies.repos)
    return _build_organizer_page(
        pipeline_model=pipeline_model,
        progress_dialog=progress_dialog,
        scan_extensions=scan_extensions,
        include_companion_subtitles=include_companion_subtitles,
        exclude_subtitles_with_paired_video=exclude_subtitles_with_paired_video,
        dependencies=dependencies,
        tmdb_runtime=tmdb_runtime,
    )


def _build_organizer_page(
    *,
    pipeline_model: PipelineTableModel | None,
    progress_dialog: ProgressDialog | None,
    scan_extensions: tuple[str, ...] | None,
    include_companion_subtitles: bool,
    dependencies: _OrganizerDependencies,
    tmdb_runtime: _TmdbRuntime | None,
    exclude_subtitles_with_paired_video: bool = False,
) -> OrganizerPage:
    model = pipeline_model if pipeline_model is not None else PipelineTableModel()
    repos = dependencies.repos
    scan_execute = (
        make_scan_execute(
            dependencies.file_repo,
            library_index=repos.library_index,
            parse_cache=repos.parse_cache,
            resolution_probe=dependencies.resolution_probe,
        )
        if scan_extensions is None
        else make_scan_execute(
            dependencies.file_repo,
            extensions=scan_extensions,
            library_index=repos.library_index,
            parse_cache=repos.parse_cache,
            resolution_probe=dependencies.resolution_probe,
        )
    )
    parse_execute = _create_parse_execute(repos)
    cached_tmdb_hydrate_execute = make_cached_tmdb_hydrate_execute(
        title_match=repos.title_match,
        title_groups=repos.title_groups,
    )

    match_execute = None
    tmdb_search_execute = None
    cached_tmdb_missing_fill_execute = None
    poster_sync: TmdbPosterAssetSync | None = None
    if tmdb_runtime is not None:
        match_execute = tmdb_runtime.match_execute
        tmdb_search_execute = tmdb_runtime.tmdb_search_execute
        cached_tmdb_missing_fill_execute = tmdb_runtime.cached_tmdb_missing_fill_execute
        poster_sync = tmdb_runtime.poster_sync

    presenter = OrganizerPresenter(
        pipeline_model=model,
        scan_execute=scan_execute,
        parse_execute=parse_execute,
        match_execute=match_execute,
        tmdb_search_execute=tmdb_search_execute,
        plan_execute=make_plan_execute(organize_plan=repos.organize_plan),
        apply_execute=make_apply_execute(
            dependencies.file_repo,
            _make_operation_log_repository,
            library_index=repos.library_index,
            organize_plan=repos.organize_plan,
        ),
        progress_dialog=progress_dialog,
        include_companion_subtitles=include_companion_subtitles,
        exclude_subtitles_with_paired_video=exclude_subtitles_with_paired_video,
        sync_title_groups_execute=make_sync_title_groups_execute(repos.title_groups),
        cached_tmdb_hydrate_execute=cached_tmdb_hydrate_execute,
        cached_tmdb_missing_fill_execute=cached_tmdb_missing_fill_execute,
        ports=OrganizerPresenterPorts(
            title_match=repos.title_match,
            title_groups=repos.title_groups,
            poster_sync=poster_sync,
        ),
    )
    return OrganizerPage(model=model, presenter=presenter)


def _create_tmdb_runtime(repos: _SqliteRepositories) -> _TmdbRuntime | None:
    api_key = (os.environ.get("TMDB_API_KEY") or read_tmdb_api_key() or "").strip()
    if not api_key:
        return None
    metadata = _create_metadata_provider(api_key, repos)
    poster_sync = TmdbPosterAssetSync(repos.title_match, default_poster_cache_dir())
    return _TmdbRuntime(
        metadata=metadata,
        poster_sync=poster_sync,
        match_execute=make_match_execute(
            metadata,
            title_match=repos.title_match,
            title_groups=repos.title_groups,
            poster_sync=poster_sync.sync_from_match_result,
        ),
        tmdb_search_execute=make_tmdb_search_execute(metadata),
        cached_tmdb_missing_fill_execute=make_cached_tmdb_missing_fill_execute(
            provider=metadata,
            title_match=repos.title_match,
            title_groups=repos.title_groups,
            poster_sync=poster_sync.sync_from_match_result,
        ),
    )


def _create_sqlite_repositories() -> _SqliteRepositories:
    conn = create_connection()
    lock = threading.Lock()
    return _SqliteRepositories(
        connection=conn,
        lock=lock,
        library_index=SqliteLibraryIndexRepository(conn, lock),
        organize_plan=SqliteOrganizePlanRepository(conn, lock),
        parse_cache=SqliteParseCacheRepository(conn, lock),
        title_groups=SqliteTitleGroupRepository(conn, lock),
        title_match=SqliteTitleMatchRepository(conn, lock),
        search_tv_library=SqliteTmdbSearchTvLibraryRepository(conn, lock),
    )


def _create_parse_execute(
    repos: _SqliteRepositories,
) -> Callable[[ParseInput, Callable[[ProgressEvent], None] | None, Event], ParseResult]:
    """Return parse runner that re-reads GUI settings each run (e.g. ignore_tokens)."""

    def execute(
        input_dto: ParseInput,
        progress_callback: Callable[[ProgressEvent], None] | None,
        cancel_token: Event,
    ) -> ParseResult:
        settings = load_all()
        ignore_tokens = parse_ignore_tokens_from_loaded(settings)
        parser = AnitopyTitleParser(ignore_tokens=ignore_tokens)
        inner = make_parse_execute(
            parser,
            library_index=repos.library_index,
            parse_cache=repos.parse_cache,
        )
        return inner(input_dto, progress_callback, cancel_token)

    return execute


def _create_metadata_provider(
    api_key: str,
    repos: _SqliteRepositories,
) -> CachingMetadataProvider:
    tmdb_client = TmdbApiClient(api_key, language="ko-KR")
    persist_tv_library = make_persist_search_tv_library_execute(repos.search_tv_library)
    inner = TmdbMetadataProvider(
        tmdb_client,
        persist_search_tv_library=persist_tv_library,
    )
    return CachingMetadataProvider(
        inner,
        repos.title_match,
        language="ko-KR",
    )


def _make_operation_log_repository(root: Path) -> OperationLogRepository:
    return FsOperationLogRepository(root)
