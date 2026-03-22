"""plan_helpers.py

PipelineRow에서 PlanInput 구성·플랜 적용 후 모델 병합. Presenter 간 중복 방지.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Any

from anivault.application.dto.match_result import MatchFileRow
from anivault.application.dto.plan import PlanInput, PlanResult
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel, group_pipeline_rows


def pipeline_row_to_match_file(row: PipelineRow) -> MatchFileRow:
    """PipelineRow를 MatchFileRow DTO로 변환한다.

    Args:
        row: 파이프라인 테이블 행.

    Returns:
        매칭·플랜 입력용 파일 행.
    """
    return MatchFileRow(
        original_file=row.original_file,
        parsed_title=row.parsed_title,
        parse_group=row.parse_group,
        tmdb_korean_title_group=row.tmdb_korean_title_group,
        tmdb_series_id=row.tmdb_series_id,
        tmdb_poster_path=row.tmdb_poster_path,
        tmdb_backdrop_path=row.tmdb_backdrop_path,
        year=row.year,
        season=row.season,
        resolution=row.resolution,
        status=row.status,
        poster_url=row.poster_url,
        backdrop_url=row.backdrop_url,
        target_path=row.target_path,
    )


def try_build_plan_input_from_settings(
    rows: list[PipelineRow],
    path_rules: dict[str, Any],
) -> tuple[PlanInput | None, str | None]:
    """path_rules와 파이프라인 행으로 PlanInput을 만든다.

    Args:
        rows: 평탄화된 파이프라인 행.
        path_rules: Settings의 path_rules 섹션.

    Returns:
        (PlanInput, None) 또는 (None, 오류 키: empty | path_rules).
    """
    if not rows:
        return None, "empty"
    tpl = (str(path_rules.get("path_template") or "")).strip()
    target_root = (str(path_rules.get("target_root") or "")).strip()
    if not tpl or not target_root:
        return None, "path_rules"
    files = tuple(pipeline_row_to_match_file(r) for r in rows)
    return (
        PlanInput(
            files=files,
            path_template=tpl,
            target_root=target_root,
            unknown_resolution=(str(path_rules.get("unknown_resolution") or "Unknown")).strip()
            or "Unknown",
            unknown_group_folder=(
                str(path_rules.get("unknown_group_folder") or "Needs_Review")
            ).strip()
            or "Needs_Review",
        ),
        None,
    )


def merge_plan_into_pipeline_rows(model: PipelineTableModel, plan: PlanResult) -> None:
    """적용된 이동을 파이프라인 행의 target_path·status에 반영한다.

    Args:
        model: 파이프라인 테이블 모델.
        plan: 적용된 계획.

    Returns:
        None.
    """
    src_to_dest = {op.source_path: op.destination_path for op in plan.moves}
    rows = model.flat_rows()
    merged: list[PipelineRow] = []
    for row in rows:
        if row.original_file in src_to_dest:
            merged.append(
                PipelineRow(
                    original_file=row.original_file,
                    parsed_title=row.parsed_title,
                    parse_group=row.parse_group,
                    tmdb_korean_title_group=row.tmdb_korean_title_group,
                    tmdb_series_id=row.tmdb_series_id,
                    tmdb_poster_path=row.tmdb_poster_path,
                    tmdb_backdrop_path=row.tmdb_backdrop_path,
                    year=row.year,
                    season=row.season,
                    resolution=row.resolution,
                    status="이동됨",
                    poster_url=row.poster_url,
                    backdrop_url=row.backdrop_url,
                    target_path=src_to_dest[row.original_file],
                )
            )
        else:
            merged.append(row)
    model.set_rows(group_pipeline_rows(merged))
