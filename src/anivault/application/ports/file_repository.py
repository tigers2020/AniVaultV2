"""file_repository.py

파일 시스템 접근 포트. 유스케이스는 이 Protocol에만 의존하고 어댑터가 구현한다.

Author: Pom Kim
"""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class FileRepository(Protocol):
    """파일 시스템 접근 계약. 스캔·이동·복사 등."""

    def list_files(
        self,
        directory: Path,
        *,
        extensions: tuple[str, ...] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[int, str | None], None] | None = None,
        sort: bool = True,
    ) -> list[Path]:
        """디렉터리 내 대상 파일 목록을 반환한다.

        Args:
            self: 파일 저장소 인스턴스.
            directory: 스캔할 디렉터리.
            extensions: 허용 확장자 튜플. None이면 구현체 기본.
            recursive: 하위 디렉터리 포함 여부.
            progress_callback: 진행 시 (현재 개수, 항목 경로) 호출. None이면 생략.
            sort: True면 경로 문자열 기준 정렬. False면 수집 순서(구현체 의존).

        Returns:
            발견된 파일 경로 목록.
        """
        ...

    def move(self, source: Path, destination: Path) -> None:
        """파일 또는 디렉터리를 이동한다.

        Args:
            self: 파일 저장소 인스턴스.
            source: 원본 경로.
            destination: 대상 경로.

        Returns:
            None.
        """
        ...

    def copy(self, source: Path, destination: Path) -> None:
        """파일 또는 디렉터리를 복사한다.

        Args:
            self: 파일 저장소 인스턴스.
            source: 원본 경로.
            destination: 대상 경로.

        Returns:
            None.
        """
        ...
