"""Progress stage and shared progress constants."""

from __future__ import annotations

from typing import Final

PROGRESS_STAGE_SCAN: Final[str] = "scan"
PROGRESS_STAGE_PARSE: Final[str] = "parse"
PROGRESS_STAGE_MATCH: Final[str] = "match"
PROGRESS_STAGE_PLAN: Final[str] = "plan"
PROGRESS_STAGE_APPLY: Final[str] = "apply"
PROGRESS_STAGE_ROLLBACK: Final[str] = "rollback"

PROGRESS_PERCENT_MAX: Final[int] = 100
