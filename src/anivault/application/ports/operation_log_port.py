"""operation_log_port.py

작업 로그 포트: 계획 저장·로드(롤백용). 유스케이스는 이 Protocol에만 의존하고 어댑터가 구현한다.

Author: Pom Kim
"""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class OperationLogRepository(Protocol):
    """작업 로그 저장/조회 계약. apply 전 저장, rollback 시 로드."""

    def save_plan(self, operations: list[object]) -> Path:
        """계획을 타임스탬프 로그 파일에 저장한다.

        Args:
            self: 작업 로그 저장소 인스턴스.
            operations: 저장할 작업(이동 등) 객체 목록.

        Returns:
            생성된 로그 파일 경로.
        """
        ...

    def load_plan(self, log_path: Path) -> list[object]:
        """로그 파일에서 작업 목록을 복원한다.

        Args:
            self: 작업 로그 저장소 인스턴스.
            log_path: 로그 파일 경로.

        Returns:
            복원된 작업 객체 목록.

        Raises:
            OSError 등: 파일 없음·손상 시 어댑터 구현에 따른 예외.
        """
        ...
