"""cache_port.py

캐시 포트(TMDB 검색 결과 등). 유스케이스는 이 Protocol에만 의존하고 어댑터가 구현한다.

Author: Pom Kim
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class CacheRepository(Protocol):
    """캐시 계약. 오프라인·중복 요청 감소용."""

    def get(self, key: str) -> object | None:
        """키에 해당하는 값을 반환한다.

        Args:
            self: 캐시 저장소 인스턴스.
            key: 조회 키.

        Returns:
            저장된 값. 없으면 None.
        """
        ...

    def set(self, key: str, value: object, *, ttl_seconds: int | None = None) -> None:
        """키-값을 저장한다.

        Args:
            self: 캐시 저장소 인스턴스.
            key: 저장 키.
            value: 저장할 값.
            ttl_seconds: 만료 시간(초). None이면 구현체 기본 동작.

        Returns:
            None.
        """
        ...
