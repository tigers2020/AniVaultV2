"""__init__.py

페이지: organizer, operations, settings(organism만 조합).

Author: Pom Kim
"""

from anivault.interfaces.gui.pages.operations_page import OperationsPage
from anivault.interfaces.gui.pages.organizer_page import OrganizerPage
from anivault.interfaces.gui.pages.settings_page import SettingsPage

__all__ = ["OrganizerPage", "OperationsPage", "SettingsPage"]
