"""Application ports (protocols). Adapters implement these; use cases depend on them."""

from anivault.application.ports.cache_port import CacheRepository
from anivault.application.ports.file_repository import FileRepository
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.operation_log_port import OperationLogRepository

__all__ = [
    "CacheRepository",
    "FileRepository",
    "MetadataProvider",
    "OperationLogRepository",
]
