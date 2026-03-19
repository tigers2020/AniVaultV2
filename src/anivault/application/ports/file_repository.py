"""Port: file system access. Use cases depend on this; adapters implement it."""

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
    ) -> list[Path]:
        """디렉터리 내 대상 파일 목록 반환. progress_callback(current_count, item_path) 호출 가능."""
        ...

    def move(self, source: Path, destination: Path) -> None:
        """파일/디렉터리 이동."""
        ...

    def copy(self, source: Path, destination: Path) -> None:
        """파일/디렉터리 복사."""
        ...
