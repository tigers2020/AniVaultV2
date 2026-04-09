"""Dependency wiring for GUI pages, use cases, and adapters."""

from __future__ import annotations

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any, cast

from anivault.adapters.fs import FsFileRepository
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
from anivault.application.dto.parse import ParseInput, ParseResult
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.library_index_port import LibraryIndexRepository
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
    tuple[TmdbSeriesCandidateDTO, ...],
]


@dataclass(frozen=True)
class _SqliteRepositories:
    library_index: SqliteLibraryIndexRepository
    organize_plan: SqliteOrganizePlanRepository
    parse_cache: SqliteParseCacheRepository
    title_groups: SqliteTitleGroupRepository
    title_match: SqliteTitleMatchRepository
    search_tv_library: SqliteTmdbSearchTvLibraryRepository


def make_tmdb_search_execute(provider: MetadataProvider) -> TmdbSearchExecute:
    """Create a background-safe TMDB search execute function from a metadata provider."""

    def execute(
        input_dto: TmdbSearchInput,
        progress_callback: Callable[[ProgressEvent], None] | None,
        cancel_token: Event,
    ) -> tuple[TmdbSeriesCandidateDTO, ...]:
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


def _create_organizer_page(
    *,
    pipeline_model: PipelineTableModel | None,
    progress_dialog: ProgressDialog | None,
    scan_extensions: tuple[str, ...] | None,
    include_companion_subtitles: bool,
    exclude_subtitles_with_paired_video: bool = False,
) -> OrganizerPage:
    model = pipeline_model if pipeline_model is not None else PipelineTableModel()
    file_repo = FsFileRepository()
    repos = _create_sqlite_repositories()
    library_index_repo = cast(LibraryIndexRepository, repos.library_index)
    scan_execute = (
        make_scan_execute(file_repo, library_index=library_index_repo)
        if scan_extensions is None
        else make_scan_execute(
            file_repo,
            extensions=scan_extensions,
            library_index=library_index_repo,
        )
    )
    parse_execute = _create_parse_execute(repos)
    cached_tmdb_hydrate_execute = make_cached_tmdb_hydrate_execute(
        title_match=repos.title_match,
        title_groups=repos.title_groups,
    )
    cached_tmdb_missing_fill_execute = None
    match_execute = None
    tmdb_search_execute = None
    poster_sync: TmdbPosterAssetSync | None = None
    api_key = (os.environ.get("TMDB_API_KEY") or read_tmdb_api_key() or "").strip()
    if api_key:
        metadata = _create_metadata_provider(api_key, repos)
        poster_sync = TmdbPosterAssetSync(repos.title_match, default_poster_cache_dir())
        match_execute = make_match_execute(
            metadata,
            title_match=repos.title_match,
            title_groups=repos.title_groups,
            poster_sync=poster_sync.sync_from_match_result,
        )
        cached_tmdb_missing_fill_execute = make_cached_tmdb_missing_fill_execute(
            provider=metadata,
            title_match=repos.title_match,
            title_groups=repos.title_groups,
            poster_sync=poster_sync.sync_from_match_result,
        )
        tmdb_search_execute = make_tmdb_search_execute(metadata)

    presenter = OrganizerPresenter(
        pipeline_model=model,
        scan_execute=scan_execute,
        parse_execute=parse_execute,
        match_execute=match_execute,
        tmdb_search_execute=tmdb_search_execute,
        plan_execute=make_plan_execute(organize_plan=repos.organize_plan),
        apply_execute=make_apply_execute(
            file_repo,
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


def _create_sqlite_repositories() -> _SqliteRepositories:
    conn = create_connection()
    lock = threading.Lock()
    return _SqliteRepositories(
        library_index=SqliteLibraryIndexRepository(conn, lock),
        organize_plan=SqliteOrganizePlanRepository(conn, lock),
        parse_cache=SqliteParseCacheRepository(conn, lock),
        title_groups=SqliteTitleGroupRepository(conn, lock),
        title_match=SqliteTitleMatchRepository(conn, lock),
        search_tv_library=SqliteTmdbSearchTvLibraryRepository(conn, lock),
    )


def _create_parse_execute(
    repos: _SqliteRepositories,
) -> Callable[[ParseInput, object, Any], ParseResult]:
    settings = load_all()
    ignore_tokens = parse_ignore_tokens_from_loaded(settings)
    parser = AnitopyTitleParser(ignore_tokens=ignore_tokens)
    return make_parse_execute(
        parser,
        library_index=cast(LibraryIndexRepository, repos.library_index),
        parse_cache=repos.parse_cache,
    )


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
