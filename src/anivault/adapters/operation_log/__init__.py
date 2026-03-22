"""__init__.py

작업 로그 어댑터(OperationLogRepository). 이동 계획 저장·롤백용 로드.

Author: Pom Kim
"""

from anivault.adapters.operation_log.fs_operation_log import FsOperationLogRepository

__all__ = ["FsOperationLogRepository"]
