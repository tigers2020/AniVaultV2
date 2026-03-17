"""
Composition root for GUI. Creates presenters and use cases.
Start simple; expand when DI container is needed.
"""

from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.pages import OrganizerPage, OperationsPage, SettingsPage
from anivault.interfaces.gui.presenters import (
    OrganizerPresenter,
    OperationsPresenter,
    SettingsPresenter,
)


def create_organizer_page() -> OrganizerPage:
    """Create OrganizerPage with presenter and shared model."""
    model = PipelineTableModel()
    return OrganizerPage(model=model, presenter=OrganizerPresenter(pipeline_model=model))


def create_operations_page() -> OperationsPage:
    """Create OperationsPage with presenter."""
    return OperationsPage(presenter=OperationsPresenter())


def create_settings_page() -> SettingsPage:
    """Create SettingsPage with presenter."""
    return SettingsPage(presenter=SettingsPresenter())
