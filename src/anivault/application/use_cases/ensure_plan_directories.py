"""ensure_plan_directories.py

플랜에 포함된 목적지 경로의 상위 디렉터리만 생성한다. 파일 이동은 하지 않는다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Event

from anivault.application.dto.progress import ProgressEvent
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_APPLY
from anivault.domain.models import FileOperation

ProgressCallback = Callable[[ProgressEvent], None] | None


@dataclass(slots=True)
class EnsureDirsInput:
    """디렉터리 생성 입력."""

    operations: tuple[FileOperation, ...]


@dataclass(slots=True)
class EnsureDirsResult:
    """디렉터리 생성 결과."""

    created_count: int
    error: str | None = None


def execute(
    input_dto: EnsureDirsInput,
    progress_callback: ProgressCallback,
    cancel_token: Event,
) -> EnsureDirsResult:
    """각 목적지의 parent 디렉터리를 만든다.

    Args:
        input_dto: FileOperation 목록.
        progress_callback: 진행률 콜백.
        cancel_token: 설정 시 중단.

    Returns:
        생성한 디렉터리 수(파일당 1회 카운트) 및 오류.
    """
    ops = list(input_dto.operations)
    if not ops:
        return EnsureDirsResult(created_count=0, error="작업이 없습니다.")

    total = len(ops)
    created = 0
    for i, op in enumerate(ops):
        if cancel_token.is_set():
            return EnsureDirsResult(created_count=created, error="취소되었습니다.")
        try:
            Path(op.destination_path).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return EnsureDirsResult(created_count=created, error=str(e))
        created += 1
        if progress_callback is not None:
            cur = i + 1
            progress_callback(
                ProgressEvent(
                    stage=PROGRESS_STAGE_APPLY,
                    current=cur,
                    total=total,
                    message=f"폴더 생성 중 ({cur}/{total})",
                    percent=int(PROGRESS_PERCENT_MAX * cur / total),
                    item_path=str(Path(op.destination_path).parent),
                )
            )

    return EnsureDirsResult(created_count=created)
