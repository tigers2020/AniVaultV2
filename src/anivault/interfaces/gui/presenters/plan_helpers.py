"""plan_helpers.py

PipelineRow에서 PlanInput 구성·플랜 적용 후 모델 병합. Presenter 간 중복 방지.

Author: Pom Kim
"""

from __future__ import annotations

import os
from typing import Any

from anivault.application.dto.match_result import MatchFileRow
from anivault.application.dto.plan import PlanInput, PlanResult
from anivault.interfaces.gui.models import (
    PipelineRow,
    PipelineTableModel,
    group_pipeline_rows,
    pipeline_rows_ready_for_plan,
)


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
        episode=row.episode,
    )


def try_build_plan_input_from_settings(
    rows: list[PipelineRow],
    path_rules: dict[str, Any],
    *,
    include_companion_subtitles: bool = True,
) -> tuple[PlanInput | None, str | None]:
    """path_rules와 파이프라인 행으로 PlanInput을 만든다.

    Args:
        rows: 평탄화된 파이프라인 행.
        path_rules: Settings의 path_rules 섹션.
        include_companion_subtitles: True면 플랜에 동반 자막 이동을 포함한다.

    Returns:
        (PlanInput, None) 또는 (None, 오류 키: empty | no_matched | path_rules).
    """
    if not rows:
        return None, "empty"
    ready = pipeline_rows_ready_for_plan(rows)
    if not ready:
        return None, "no_matched"
    tpl = (str(path_rules.get("path_template") or "")).strip()
    target_root = (str(path_rules.get("target_root") or "")).strip()
    if not tpl or not target_root:
        return None, "path_rules"
    files = tuple(pipeline_row_to_match_file(r) for r in ready)
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
            include_companion_subtitles=include_companion_subtitles,
        ),
        None,
    )


def _merge_path_key(path: str) -> str:
    """플랜 병합 시 경로 동일성 판별용 정규화 키를 만든다.

    Args:
        path: 원본 경로 문자열.

    Returns:
        정규화된 비교 키(실패 시 입력을 그대로 반환).
    """
    try:
        return os.path.normcase(os.path.normpath(path))
    except (TypeError, ValueError):
        return path


def merge_plan_into_pipeline_rows(model: PipelineTableModel, plan: PlanResult) -> None:
    """적용된 이동을 파이프라인 행의 target_path·status에 반영한다.

    Args:
        model: 파이프라인 테이블 모델.
        plan: 적용된 계획.

    Returns:
        None.
    """
    src_to_dest: dict[str, str] = {}
    for op in plan.moves:
        src_to_dest[_merge_path_key(op.source_path)] = op.destination_path
    rows = model.flat_rows()
    merged: list[PipelineRow] = []
    for row in rows:
        lookup = _merge_path_key(row.original_file)
        if lookup in src_to_dest:
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
                    target_path=src_to_dest[lookup],
                    episode=row.episode,
                )
            )
        else:
            merged.append(row)
    model.set_rows(group_pipeline_rows(merged))
