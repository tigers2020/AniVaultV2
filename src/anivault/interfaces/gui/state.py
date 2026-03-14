"""Minimal GUI state: current tab, selected row id, preview data. No over-engineering."""

from dataclasses import dataclass
from typing import Any


@dataclass
class GuiState:
    """Current tab, selected pipeline row index, optional preview payload."""

    current_tab: str = "organizer"
    selected_row_index: int = -1
    preview_data: Any = None
