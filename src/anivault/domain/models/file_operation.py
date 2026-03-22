"""file_operation.py

파일 이동·복사 등 계획/로그용 도메인 단위 작업.

Author: Pom Kim
"""

from dataclasses import dataclass
from enum import Enum


class OperationType(str, Enum):
    """작업 유형."""

    MOVE = "MOVE"
    COPY = "COPY"


@dataclass(slots=True)
class FileOperation:
    """단일 파일 작업(apply·operation log 직렬화)."""

    operation_type: OperationType
    source_path: str
    destination_path: str
