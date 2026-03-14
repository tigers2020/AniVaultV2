"""Port: operation log (save/load plan for rollback). Use cases depend on this; adapters implement it."""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class OperationLogRepository(Protocol):
    """작업 로그 저장/조회 계약. apply 전 저장, rollback 시 로드."""

    def save_plan(self, operations: list[object]) -> Path:
        """계획을 타임스탬프 로그 파일에 저장. 반환: 생성된 로그 파일 경로."""
        ...

    def load_plan(self, log_path: Path) -> list[object]:
        """로그 파일에서 작업 목록 복원. 파일 없음/손상 시 예외."""
        ...
