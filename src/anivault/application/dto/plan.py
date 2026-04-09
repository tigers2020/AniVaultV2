"""plan.py

이동 계획(plan)·적용(apply) 유스케이스 입·출력 DTO.

Author: Pom Kim
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from anivault.application.dto.match_result import MatchFileRow
from anivault.domain.models import FileOperation, PathTemplateInput


class _GroupableMatchRow(Protocol):
    original_file: str
    parsed_title: str
    tmdb_korean_title_group: str
    tmdb_series_id: str


def match_file_row_to_path_template_input(row: MatchFileRow) -> PathTemplateInput:
    """MatchFileRow를 경로 템플릿 입력으로 변환한다.

    Args:
        row: 매칭된 파일 행.

    Returns:
        PathTemplateInput.
    """
    return PathTemplateInput(
        original_file=row.original_file,
        resolution=row.resolution,
        year=row.year,
        season=row.season,
        korean_title_group=row.tmdb_korean_title_group,
    )


def match_file_row_group_key(row: _GroupableMatchRow) -> str:
    """Return the shared pipeline grouping key for a matched row."""
    tmdb_series_id = (row.tmdb_series_id or "").strip()
    if tmdb_series_id:
        return f"tmdb:{tmdb_series_id}"
    parsed_title = (row.parsed_title or "").strip()
    if parsed_title:
        return parsed_title
    return row.original_file


def match_file_row_group_label(row: _GroupableMatchRow) -> str:
    """Return the user-facing label for preview groups."""
    group_title = (row.tmdb_korean_title_group or "").strip()
    if group_title:
        return group_title
    parsed_title = (row.parsed_title or "").strip()
    if parsed_title:
        return parsed_title
    return Path(row.original_file).name


@dataclass(slots=True, frozen=True)
class PlanMovePreviewMeta:
    """Preview metadata for grouping dry-run items."""

    group_key: str
    group_label: str
    resolution_segment: str


@dataclass(slots=True)
class PlanInput:
    """이동 계획 생성 입력."""

    files: tuple[MatchFileRow, ...]
    path_template: str
    target_root: str
    unknown_resolution: str
    unknown_group_folder: str
    include_companion_subtitles: bool = True
    index_root_id: int | None = None


@dataclass(slots=True)
class PlanResult:
    """이동 계획 생성 결과."""

    moves: tuple[FileOperation, ...] = field(default_factory=tuple)
    move_preview: tuple[PlanMovePreviewMeta, ...] = field(default_factory=tuple)
    error: str | None = None
    organize_plan_id: int | None = None
    organize_item_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ApplyInput:
    """계획 적용 입력."""

    operations: tuple[FileOperation, ...]
    dry_run: bool
    log_root: str
    source_root: str | None = None
    index_root_id: int | None = None
    organize_plan_id: int | None = None
    organize_item_ids: tuple[int, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ApplyResult:
    """계획 적용 결과."""

    log_path: Path | None
    moved_count: int
    error: str | None = None
