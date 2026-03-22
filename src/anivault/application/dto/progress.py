"""progress.py

장시간 유스케이스(scan/match/plan/apply/rollback)용 진행 이벤트 DTO.

Author: Pom Kim
"""

from dataclasses import dataclass


@dataclass
class ProgressEvent:
    """스캔·매칭 등 단계별 진행 상태."""

    stage: str  # "scan" | "match" | "plan" | "apply" | "rollback"
    current: int
    total: int
    message: str
    percent: int
    item_path: str | None = None


def progress_dialog_value_and_maximum(event: ProgressEvent) -> tuple[int | None, int]:
    """ProgressEvent를 QProgressBar에 넣을 (값, 최댓값)으로 변환한다.

    total이 0이면 확정 구간이 아니므로 값은 갱신하지 않고(None), 최댓값은 100으로 둔다.

    Args:
        event: 유스케이스에서 보낸 진행 이벤트.

    Returns:
        (막대 값 또는 None, setMaximum에 쓸 정수).
    """
    if event.total > 0:
        return event.current, event.total
    return None, 100
