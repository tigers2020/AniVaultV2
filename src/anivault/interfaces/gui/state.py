"""state.py

최소 GUI 상태: 현재 탭, 선택 행, 미리보기 데이터.

Author: Pom Kim
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class GuiState:
    """현재 탭, 파이프라인 선택 행 인덱스, 선택적 미리보기 페이로드."""

    current_tab: str = "organizer"
    selected_row_index: int = -1
    preview_data: Any = None
