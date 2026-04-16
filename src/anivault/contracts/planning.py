"""Planning and apply contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from anivault.contracts.pipeline import PipelineRow
from anivault.domain.models import FileOperation


@dataclass(slots=True, frozen=True)
class PlanMovePreviewMeta:
    """Preview metadata for grouping dry-run items."""

    group_key: str
    group_label: str
    resolution_segment: str


@dataclass(slots=True)
class PlanInput:
    """Input for move planning."""

    files: tuple[PipelineRow, ...]
    path_template: str
    target_root: str
    unknown_resolution: str
    unknown_group_folder: str
    include_companion_subtitles: bool = True
    index_root_id: int | None = None


@dataclass(slots=True)
class PlanResult:
    """Output for move planning."""

    moves: tuple[FileOperation, ...] = field(default_factory=tuple)
    move_preview: tuple[PlanMovePreviewMeta, ...] = field(default_factory=tuple)
    error: str | None = None
    organize_plan_id: int | None = None
    organize_item_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ApplyInput:
    """Input for plan application."""

    operations: tuple[FileOperation, ...]
    dry_run: bool
    source_root: str | None = None
    index_root_id: int | None = None
    organize_plan_id: int | None = None
    organize_item_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ApplyResult:
    """Output for plan application."""

    log_path: Path | None
    moved_count: int
    error: str | None = None
