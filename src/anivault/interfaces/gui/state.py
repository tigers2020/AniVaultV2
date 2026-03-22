"""state.py

GUI 상태: 탭, 선택, 미리보기, Operations 단계.

Author: Pom Kim
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OperationsPhase(str, Enum):
    """Operations 탭 장시간 작업 단계(표시·로깅용)."""

    idle = "idle"
    planning = "planning"
    applying = "applying"
    mkdir = "mkdir"
    rolling_back = "rolling_back"
    error = "error"


@dataclass
class GuiState:
    """현재 탭, 파이프라인 선택, 미리보기, Operations 단계."""

    current_tab: str = "organizer"
    selected_row_index: int = -1
    preview_data: Any = None
    operations_phase: OperationsPhase = OperationsPhase.idle
