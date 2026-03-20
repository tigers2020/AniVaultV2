"""
Composition root for GUI. Creates presenters and use cases.
Start simple; expand when DI container is needed.
"""

import os
from typing import TYPE_CHECKING

from anivault.adapters.fs import FsFileRepository
from anivault.adapters.metadata.tmdb import TmdbApiClient, TmdbMetadataProvider
from anivault.adapters.parser import AnitopyTitleParser
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
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

if TYPE_CHECKING:
    from anivault.interfaces.gui.components.molecules import ProgressDialog


def create_organizer_page(
    progress_dialog: "ProgressDialog | None" = None,
) -> OrganizerPage:
    """Create OrganizerPage with presenter and shared model."""
    model = PipelineTableModel()
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
    presenter = OrganizerPresenter(
        pipeline_model=model,
        scan_execute=scan_execute,
        parse_execute=parse_execute,
        match_execute=match_execute,
        progress_dialog=progress_dialog,
    )
    return OrganizerPage(model=model, presenter=presenter)


def create_operations_page() -> OperationsPage:
    """Create OperationsPage with presenter."""
    return OperationsPage(presenter=OperationsPresenter())


def create_settings_page() -> SettingsPage:
    """Create SettingsPage with presenter."""
    return SettingsPage(presenter=SettingsPresenter())
