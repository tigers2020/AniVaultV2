"""composition.py

GUI 조립 루트: Presenter·유스케이스·어댑터 생성. DI 컨테이너 전 단계.

Author: Pom Kim
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING

from anivault.adapters.fs import FsFileRepository
from anivault.adapters.metadata.tmdb import TmdbApiClient, TmdbMetadataProvider
from anivault.adapters.operation_log import FsOperationLogRepository
from anivault.adapters.parser import AnitopyTitleParser
from anivault.application.ports.operation_log_port import OperationLogRepository
from anivault.application.use_cases.apply_plan import make_apply_execute
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
from anivault.application.use_cases.plan_moves import make_execute as make_plan_execute
from anivault.application.use_cases.scan_library import make_execute
from anivault.bootstrap.env_file import read_tmdb_api_key
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.pages import OperationsPage, OrganizerPage, SettingsPage
from anivault.interfaces.gui.presenters import (
    OperationsPresenter,
    OrganizerPresenter,
    SettingsPresenter,
)
from anivault.interfaces.gui.settings_storage import load_all
from anivault.interfaces.gui.state import GuiState

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog


def create_organizer_page(
    pipeline_model: PipelineTableModel | None = None,
    progress_dialog: "ProgressDialog | None" = None,
) -> OrganizerPage:
    """스캔·파싱·매칭 유스케이스와 OrganizerPresenter를 주입한 페이지를 만든다.

    Args:
        pipeline_model: Organizer·Operations가 공유할 모델. None이면 새로 만든다.
        progress_dialog: 진행 대화상자(선택).

    Returns:
        OrganizerPage.
    """
    model = pipeline_model if pipeline_model is not None else PipelineTableModel()
    file_repo = FsFileRepository()
    scan_execute = make_execute(file_repo)
    settings = load_all()
    ignore_tokens = settings.get("parse_tmdb", {}).get("ignore_tokens", "") or ""
    parser = AnitopyTitleParser(ignore_tokens=ignore_tokens)
    parse_execute = make_parse_execute(parser)
    api_key = (os.environ.get("TMDB_API_KEY") or read_tmdb_api_key() or "").strip()
    match_execute = None
    if api_key:
        tmdb_client = TmdbApiClient(api_key, language="ko-KR")
        metadata = TmdbMetadataProvider(tmdb_client)
        match_execute = make_match_execute(metadata)

    def _make_op_log(root: Path) -> OperationLogRepository:
        """log_root별 OperationLogRepository를 만든다.

        Args:
            root: `.anivault/logs` 상위 디렉터리.

        Returns:
            FsOperationLogRepository 인스턴스.
        """
        return FsOperationLogRepository(root)

    plan_execute = make_plan_execute()
    apply_execute = make_apply_execute(file_repo, _make_op_log)
    presenter = OrganizerPresenter(
        pipeline_model=model,
        scan_execute=scan_execute,
        parse_execute=parse_execute,
        match_execute=match_execute,
        plan_execute=plan_execute,
        apply_execute=apply_execute,
        progress_dialog=progress_dialog,
    )
    return OrganizerPage(model=model, presenter=presenter)


def create_operations_page(
    pipeline_model: PipelineTableModel,
    progress_dialog: "ProgressDialog | None" = None,
    gui_state: GuiState | None = None,
) -> OperationsPage:
    """플랜·적용 유스케이스와 OperationsPresenter를 주입한 페이지를 만든다.

    Args:
        pipeline_model: Organizer와 동일한 파이프라인 모델.
        progress_dialog: 진행 대화상자(선택).
        gui_state: Operations 단계 표시용 전역 상태(선택).

    Returns:
        OperationsPage.
    """
    file_repo = FsFileRepository()

    def _make_op_log(root: Path) -> OperationLogRepository:
        """log_root별 OperationLogRepository를 만든다.

        Args:
            root: `.anivault/logs` 상위 디렉터리.

        Returns:
            FsOperationLogRepository 인스턴스.
        """
        return FsOperationLogRepository(root)

    plan_execute = make_plan_execute()
    apply_execute = make_apply_execute(file_repo, _make_op_log)
    presenter = OperationsPresenter(
        pipeline_model=pipeline_model,
        plan_execute=plan_execute,
        apply_execute=apply_execute,
        gui_state=gui_state,
        progress_dialog=progress_dialog,
    )
    return OperationsPage(presenter=presenter)


def create_settings_page() -> SettingsPage:
    """SettingsPresenter를 주입한 SettingsPage를 만든다.

    Args:
        없음.

    Returns:
        SettingsPage.
    """
    return SettingsPage(presenter=SettingsPresenter())
