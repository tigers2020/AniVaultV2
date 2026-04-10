"""Compatibility shim for the legacy SQLite ``app_kv`` cache adapter."""

from anivault.adapters.persistence.sqlite.legacy_cache_repository import (
    SqliteCacheRepository,
    _is_expired,
    _ttl_to_expires_at,
)

__all__ = ["SqliteCacheRepository", "_is_expired", "_ttl_to_expires_at"]
