"""composition.py

GUI 조립 루트: Presenter·유스케이스·어댑터 생성. DI 컨테이너 전 단계.

Author: Pom Kim
"""

import os
import threading
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Literal

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
    create_connection,
)
from anivault.adapters.persistence.sqlite.db_path import default_poster_cache_dir
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.operation_log_port import OperationLogRepository
from anivault.application.use_cases.apply_plan import make_apply_execute
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
from anivault.application.use_cases.plan_moves import make_execute as make_plan_execute
from anivault.application.use_cases.scan_library import make_execute
from anivault.application.use_cases.sync_title_groups import (
    make_execute as make_sync_title_groups_execute,
)
from anivault.bootstrap.env_file import read_tmdb_api_key
from anivault.domain.media.extensions import SUBTITLE_SCAN_EXTENSIONS
from anivault.domain.rules.tmdb_search_query import iter_strip_last_word_chain
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.pages import OrganizerPage, SettingsPage
from anivault.interfaces.gui.presenters import OrganizerPresenter, SettingsPresenter
from anivault.interfaces.gui.settings_storage import load_all

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog

OrganizerPageMode = Literal["video", "subtitle"]


def make_tmdb_search_execute(
    provider: MetadataProvider,
) -> Callable[
    [TmdbSearchInput, Callable[[ProgressEvent], None] | None, Event],
    tuple[TmdbSeriesCandidateDTO, ...],
]:
    """MetadataProvider로 TMDB 시리즈 검색을 백그라운드에서 실행하는 `execute`를 만든다.

    Args:
        provider: 메타데이터 검색 포트.

    Returns:
        (input_dto, progress_callback, cancel_token) -> 후보 튜플.
    """

    def execute(
        input_dto: TmdbSearchInput,
        progress_callback: Callable[[ProgressEvent], None] | None,
        cancel_token: Event,
    ) -> tuple[TmdbSeriesCandidateDTO, ...]:
        """검색어로 시리즈 후보를 조회한다.

        Args:
            input_dto: 검색어·연도.
            progress_callback: 미사용(시그니처 호환).
            cancel_token: 설정 시 빈 튜플.

        Returns:
            TMDB 후보 튜플.
        """
        del progress_callback
        if cancel_token.is_set():
            return ()
        q = (input_dto.query or "").strip()
        if not q:
            return ()
        for attempt in iter_strip_last_word_chain(q):
            found = tuple(provider.search_series(attempt, year=input_dto.year))
            if found:
                return found
        return ()

    return execute


def create_organizer_page(
    pipeline_model: PipelineTableModel | None = None,
    progress_dialog: "ProgressDialog | None" = None,
    *,
    mode: OrganizerPageMode = "video",
) -> OrganizerPage:
    """스캔·파싱·매칭 유스케이스와 OrganizerPresenter를 주입한 페이지를 만든다.

    Args:
        pipeline_model: Organizer 파이프라인 모델. None이면 새로 만든다.
        progress_dialog: 진행 대화상자(선택).
        mode: ``video`` — 일반 미디어 스캔. ``subtitle`` — 자막 확장자만, 동반 자막 플랜 비활성.

    Returns:
        OrganizerPage.
    """
    model = pipeline_model if pipeline_model is not None else PipelineTableModel()
    file_repo = FsFileRepository()
    _db_conn = create_connection()
    _db_lock = threading.Lock()
    _library_index = SqliteLibraryIndexRepository(_db_conn, _db_lock)
    _parse_cache = SqliteParseCacheRepository(_db_conn, _db_lock)
    _title_groups = SqliteTitleGroupRepository(_db_conn, _db_lock)
    _title_match = SqliteTitleMatchRepository(_db_conn, _db_lock)
    _organize_plans = SqliteOrganizePlanRepository(_db_conn, _db_lock)
    _sync_title_groups = make_sync_title_groups_execute(_title_groups)
    _stream_resolution = FfprobeStreamResolution()
    if mode == "subtitle":
        scan_execute = make_execute(
            file_repo,
            extensions=SUBTITLE_SCAN_EXTENSIONS,
            library_index=_library_index,
            parse_cache=_parse_cache,
            resolution_probe=_stream_resolution,
        )
    else:
        scan_execute = make_execute(
            file_repo,
            library_index=_library_index,
            parse_cache=_parse_cache,
            resolution_probe=_stream_resolution,
        )
    settings = load_all()
    ignore_tokens = settings.get("parse_tmdb", {}).get("ignore_tokens", "") or ""
    parser = AnitopyTitleParser(ignore_tokens=ignore_tokens)
    parse_execute = make_parse_execute(
        parser,
        library_index=_library_index,
        parse_cache=_parse_cache,
    )
    api_key = (os.environ.get("TMDB_API_KEY") or read_tmdb_api_key() or "").strip()
    match_execute = None
    tmdb_search_execute = None
    _poster_sync: TmdbPosterAssetSync | None = None
    if api_key:
        tmdb_client = TmdbApiClient(api_key, language="ko-KR")
        _tmdb_lang = "ko-KR"
        _inner_meta = TmdbMetadataProvider(tmdb_client)
        metadata = CachingMetadataProvider(
            _inner_meta,
            _title_match,
            language=_tmdb_lang,
        )
        _poster_sync = TmdbPosterAssetSync(_title_match, default_poster_cache_dir())
        match_execute = make_match_execute(
            metadata,
            title_match=_title_match,
            title_groups=_title_groups,
            poster_sync=_poster_sync.sync_from_match_result,
        )
        tmdb_search_execute = make_tmdb_search_execute(metadata)

    def _make_op_log(root: Path) -> OperationLogRepository:
        """log_root별 OperationLogRepository를 만든다.

        Args:
            root: `.anivault/logs` 상위 디렉터리.

        Returns:
            FsOperationLogRepository 인스턴스.
        """
        return FsOperationLogRepository(root)

    plan_execute = make_plan_execute(organize_plan=_organize_plans)
    apply_execute = make_apply_execute(
        file_repo,
        _make_op_log,
        library_index=_library_index,
        organize_plan=_organize_plans,
    )
    include_companion = mode == "video"
    presenter = OrganizerPresenter(
        pipeline_model=model,
        scan_execute=scan_execute,
        parse_execute=parse_execute,
        match_execute=match_execute,
        tmdb_search_execute=tmdb_search_execute,
        plan_execute=plan_execute,
        apply_execute=apply_execute,
        progress_dialog=progress_dialog,
        include_companion_subtitles=include_companion,
        sync_title_groups_execute=_sync_title_groups,
        title_match=_title_match,
        title_groups=_title_groups,
        poster_sync=_poster_sync,
    )
    return OrganizerPage(model=model, presenter=presenter)


def create_settings_page() -> SettingsPage:
    """SettingsPresenter를 주입한 SettingsPage를 만든다.

    Args:
        없음.

    Returns:
        SettingsPage.
    """
    return SettingsPage(presenter=SettingsPresenter())
