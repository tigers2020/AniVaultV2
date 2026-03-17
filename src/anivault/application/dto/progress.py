"""Progress reporting for long-running use cases."""

from dataclasses import dataclass


@dataclass
class ProgressEvent:
    """Structured progress update from scan/match/plan/apply/rollback."""

    stage: str  # "scan" | "match" | "plan" | "apply" | "rollback"
    current: int
    total: int
    message: str
    percent: int
    item_path: str | None = None
