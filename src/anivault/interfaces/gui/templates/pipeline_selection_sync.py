"""pipeline_selection_sync.py

분할 matched/unmatched 테이블과 통합 그룹 인덱스 선택 동기화.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Literal

from anivault.interfaces.gui.components.organisms.pipeline_table import PipelineTable
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineTableModel

WhichSplitTable = Literal["matched", "unmatched"]


def unified_index_for_group(
    unified_rows: Sequence[PipelineGroupRow],
    group: PipelineGroupRow,
) -> int:
    """파생 테이블의 그룹이 통합 행 목록에서 몇 번째인지 찾는다.

    Args:
        unified_rows: 통합 그룹 행 목록.
        group: 파생 테이블에서 선택된 그룹.

    Returns:
        통합 인덱스. 없으면 -1.
    """
    if not group.members:
        return -1
    key = group.members[0].original_file
    for i, g in enumerate(unified_rows):
        if any(m.original_file == key for m in g.members):
            return i
    return -1


def sync_split_tables_selection(
    unified_rows: Sequence[PipelineGroupRow],
    unified_index: int,
    matched_model: PipelineTableModel,
    unmatched_model: PipelineTableModel,
    matched_table: PipelineTable,
    unmatched_table: PipelineTable,
) -> None:
    """통합 인덱스에 맞춰 상·하단 테이블 중 하나만 하이라이트한다.

    Args:
        unified_rows: 통합 그룹 행.
        unified_index: 통합 그룹 인덱스. 범위 밖이면 선택 해제.
        matched_model: TMDB 매칭됨 부분 모델.
        unmatched_model: 미매칭 부분 모델.
        matched_table: 상단 테이블.
        unmatched_table: 하단 테이블.

    Returns:
        None.
    """
    if unified_index < 0 or unified_index >= len(unified_rows):
        matched_table.select_row(-1)
        unmatched_table.select_row(-1)
        return
    key = unified_rows[unified_index].members[0].original_file
    for i, g in enumerate(matched_model.rows()):
        if any(m.original_file == key for m in g.members):
            matched_table.select_row(i)
            unmatched_table.select_row(-1)
            return
    for i, g in enumerate(unmatched_model.rows()):
        if any(m.original_file == key for m in g.members):
            unmatched_table.select_row(i)
            matched_table.select_row(-1)
            return
    matched_table.select_row(-1)
    unmatched_table.select_row(-1)


def on_split_table_selection(
    which: WhichSplitTable,
    row: int,
    unified_rows: Sequence[PipelineGroupRow],
    matched_model: PipelineTableModel,
    unmatched_model: PipelineTableModel,
    apply_unified_selection: Callable[[int], None],
) -> None:
    """분할 테이블 선택을 통합 인덱스로 변환해 반영한다.

    Args:
        which: "matched" 또는 "unmatched".
        row: 해당 파생 테이블의 행 인덱스.
        unified_rows: 통합 그룹 목록(패널 `_rows`와 동일 순서).
        matched_model: 매칭됨 테이블 모델.
        unmatched_model: 미매칭 테이블 모델.
        apply_unified_selection: 통합 인덱스를 UI에 반영하는 콜백.

    Returns:
        None.
    """
    model = matched_model if which == "matched" else unmatched_model
    groups = model.rows()
    if row < 0 or row >= len(groups):
        return
    uni = unified_index_for_group(unified_rows, groups[row])
    if uni >= 0:
        apply_unified_selection(uni)
