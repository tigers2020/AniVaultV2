"""composition.py

GUI 조립 루트: Presenter·유스케이스·어댑터 생성. DI 컨테이너 전 단계.

Author: Pom Kim
"""

from collections.abc import Callable
from threading import Event
from typing import TYPE_CHECKING

from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSearchInput, TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.bootstrap import container as _container
from anivault.domain.rules.tmdb_search_query import iter_strip_last_word_chain
from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.pages import OrganizerPage, SettingsPage

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog


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
) -> OrganizerPage:
    """스캔·파싱·매칭 유스케이스와 OrganizerPresenter를 주입한 페이지를 만든다.

    Args:
        pipeline_model: Organizer 파이프라인 모델. None이면 새로 만든다.
        progress_dialog: 진행 대화상자(선택).

    Returns:
        OrganizerPage.
    """
    return _container.create_organizer_page(
        pipeline_model=pipeline_model,
        progress_dialog=progress_dialog,
    )


def create_subtitle_organizer_page(
    pipeline_model: PipelineTableModel | None = None,
    progress_dialog: "ProgressDialog | None" = None,
) -> OrganizerPage:
    """자막 확장자만 스캔하고 동반 자막 플랜을 끈 Organizer 페이지를 만든다.

    Args:
        pipeline_model: 파이프라인 모델. None이면 새로 만든다.
        progress_dialog: 진행 대화상자(선택).

    Returns:
        OrganizerPage.
    """
    return _container.create_subtitle_organizer_page(
        pipeline_model=pipeline_model,
        progress_dialog=progress_dialog,
    )


def create_settings_page() -> SettingsPage:
    """SettingsPresenter를 주입한 SettingsPage를 만든다.

    Args:
        없음.

    Returns:
        SettingsPage.
    """
    return _container.create_settings_page()
