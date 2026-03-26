"""plan.py

이동 계획(plan)·적용(apply) 유스케이스 입·출력 DTO.

Author: Pom Kim
"""

from dataclasses import dataclass, field
from pathlib import Path

from anivault.application.dto.match_result import MatchFileRow
from anivault.domain.models import FileOperation, PathTemplateInput


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


@dataclass(slots=True)
class PlanInput:
    """이동 계획 생성 입력."""

    files: tuple[MatchFileRow, ...]
    path_template: str
    target_root: str
    unknown_resolution: str
    unknown_group_folder: str
    include_companion_subtitles: bool = True


@dataclass(slots=True)
class PlanResult:
    """이동 계획 생성 결과."""

    moves: tuple[FileOperation, ...] = field(default_factory=tuple)
    error: str | None = None


@dataclass(slots=True)
class ApplyInput:
    """계획 적용 입력."""

    operations: tuple[FileOperation, ...]
    dry_run: bool
    log_root: str
    source_root: str | None = None


@dataclass(slots=True)
class ApplyResult:
    """계획 적용 결과."""

    log_path: Path | None
    moved_count: int
    error: str | None = None
