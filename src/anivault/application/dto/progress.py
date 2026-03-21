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
