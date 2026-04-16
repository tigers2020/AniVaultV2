"""__init__.py

GUI 모델: 파이프라인 테이블 행 DTO·프록시 모델.

Author: Pom Kim
"""

from anivault.contracts.pipeline import PipelineRow
from anivault.interfaces.gui.models.episode_overview import (
    EpisodeSlotViewModel,
    build_episode_slot_view_models,
)
from anivault.interfaces.gui.models.episode_parsing import (
    extract_episode_numbers,
    extract_first_season_number,
)
from anivault.interfaces.gui.models.pipeline_proxy_model import PipelineProxyModel
from anivault.interfaces.gui.models.pipeline_table_model import PipelineTableModel
from anivault.interfaces.gui.models.ui_rows import (
    PipelineGroupRow,
    group_pipeline_rows,
    pipeline_group_display_image_url,
    pipeline_row_ready_for_plan,
    pipeline_rows_ready_for_plan,
)

__all__ = [
    "EpisodeSlotViewModel",
    "PipelineGroupRow",
    "PipelineRow",
    "PipelineProxyModel",
    "PipelineTableModel",
    "build_episode_slot_view_models",
    "extract_episode_numbers",
    "extract_first_season_number",
    "group_pipeline_rows",
    "pipeline_group_display_image_url",
    "pipeline_row_ready_for_plan",
    "pipeline_rows_ready_for_plan",
]
