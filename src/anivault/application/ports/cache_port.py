"""Port: cache (e.g. TMDB search results). Use cases depend on this; adapters implement it."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CacheRepository(Protocol):
    """캐시 계약. 오프라인·중복 요청 감소용."""

    def get(self, key: str) -> object | None:
        """키에 해당하는 값 반환. 없으면 None."""
        ...

    def set(self, key: str, value: object, *, ttl_seconds: int | None = None) -> None:
        """키-값 저장. ttl은 선택."""
        ...
