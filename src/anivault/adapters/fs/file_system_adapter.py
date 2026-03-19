"""File system adapter implementing FileRepository."""

from collections.abc import Callable
from pathlib import Path

from anivault.application.ports.file_repository import FileRepository

_PROGRESS_INTERVAL = 50  # report every N files during scan


class FsFileRepository(FileRepository):
    """파일시스템 기반 FileRepository 구현."""

    def list_files(
        self,
        directory: Path,
        *,
        extensions: tuple[str, ...] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[int, str | None], None] | None = None,
    ) -> list[Path]:
        """디렉터리 내 대상 파일 목록 반환. progress_callback(current_count, item_path) 주기적 호출."""
        if not directory.exists() or not directory.is_dir():
            return []
        result: list[Path] = []
        ext_set = {e.lstrip(".").lower() for e in (extensions or ())}

        def _collect(base: Path) -> None:
            try:
                for p in base.iterdir():
                    if p.is_dir():
                        if recursive:
                            _collect(p)
                    elif p.is_file() and (not ext_set or p.suffix.lstrip(".").lower() in ext_set):
                        result.append(p)
                        if progress_callback and len(result) % _PROGRESS_INTERVAL == 0:
                            progress_callback(len(result), str(p))
            except OSError:
                pass

        _collect(directory)
        if progress_callback and result:
            progress_callback(len(result), str(result[-1]))
        return sorted(result)

    def move(self, source: Path, destination: Path) -> None:
        """파일/디렉터리 이동."""
        import shutil

        shutil.move(str(source), str(destination))

    def copy(self, source: Path, destination: Path) -> None:
        """파일/디렉터리 복사."""
        import shutil

        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
