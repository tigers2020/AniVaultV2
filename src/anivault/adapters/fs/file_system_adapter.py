"""file_system_adapter.py

FileRepository 프로토콜의 로컬 파일시스템 구현.

Author: Pom Kim
"""

import os
from collections.abc import Callable
from pathlib import Path

from anivault.application.ports.file_repository import FileRepository

_PROGRESS_INTERVAL = 50  # report every N files during scan


def _extension_allowed_name(name: str, ext_set: set[str]) -> bool:
    """확장자 집합이 비었거나 파일명의 확장자가 허용되면 True.

    Args:
        name: 검사할 파일명.
        ext_set: 허용 확장자(소문자, 점 없음). 비어 있으면 전부 허용.

    Returns:
        수집 대상이면 True.
    """
    if not ext_set:
        return True
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return suffix in ext_set


def _report_progress_if_due(
    progress_callback: Callable[[int, str | None], None] | None,
    count: int,
    last_path: str,
) -> None:
    """콜백이 있고 count가 간격 배수일 때 진행률을 보고한다.

    Args:
        progress_callback: (개수, 마지막 경로) 콜백. None이면 아무 것도 안 함.
        count: 현재까지 수집된 파일 수.
        last_path: 마지막으로 추가된 경로 문자열.

    Returns:
        None.
    """
    if progress_callback is None:
        return
    if count % _PROGRESS_INTERVAL != 0:
        return
    progress_callback(count, last_path)


def _walk_collect_files(
    base: Path,
    *,
    recursive: bool,
    ext_set: set[str],
    result: list[Path],
    progress_callback: Callable[[int, str | None], None] | None,
) -> None:
    """base 아래 파일을 result에 누적한다(권한 오류는 무시).

    Args:
        base: 현재 디렉터리.
        recursive: 하위 디렉터리 재귀 여부.
        ext_set: 허용 확장자 집합.
        result: 수집 결과를 쌓을 리스트.
        progress_callback: 주기적 진행 보고 콜백.

    Returns:
        None.
    """
    try:
        with os.scandir(base) as entries:
            for entry in entries:
                try:
                    is_dir = entry.is_dir()
                except OSError:
                    continue
                if is_dir and recursive:
                    _walk_collect_files(
                        Path(entry.path),
                        recursive=recursive,
                        ext_set=ext_set,
                        result=result,
                        progress_callback=progress_callback,
                    )
                    continue
                try:
                    is_file = entry.is_file()
                except OSError:
                    continue
                if not is_file or not _extension_allowed_name(entry.name, ext_set):
                    continue
                path = Path(entry.path)
                result.append(path)
                _report_progress_if_due(progress_callback, len(result), str(path))
    except OSError:
        pass


class FsFileRepository(FileRepository):
    """os.walk에 준하는 재귀 순회로 파일을 수집한다."""

    def list_files(
        self,
        directory: Path,
        *,
        extensions: tuple[str, ...] | None = None,
        recursive: bool = True,
        progress_callback: Callable[[int, str | None], None] | None = None,
        sort: bool = True,
    ) -> list[Path]:
        """디렉터리에서 확장자 필터에 맞는 파일 목록을 반환한다.

        Args:
            self: 이 저장소.
            directory: 스캔 루트.
            extensions: 허용 확장자(점 유무 무관). None이면 전부.
            recursive: 하위 디렉터리 포함 여부.
            progress_callback: N개마다 (개수, 마지막 경로) 호출.
            sort: True면 경로 문자열 기준 정렬(O(n log n)). False면 정렬 생략.

        Returns:
            Path 목록. sort가 True면 정렬됨. 디렉터리 없으면 빈 목록.
        """
        if not directory.exists() or not directory.is_dir():
            return []
        result: list[Path] = []
        ext_set = {e.lstrip(".").lower() for e in (extensions or ())}
        _walk_collect_files(
            directory,
            recursive=recursive,
            ext_set=ext_set,
            result=result,
            progress_callback=progress_callback,
        )
        if progress_callback and result:
            progress_callback(len(result), str(result[-1]))
        if sort:
            return sorted(result)
        return result

    def move(self, source: Path, destination: Path) -> None:
        """파일 또는 디렉터리를 이동한다.

        Args:
            self: 이 저장소.
            source: 원본 경로.
            destination: 대상 경로.

        Returns:
            None.
        """
        import shutil

        shutil.move(str(source), str(destination))

    def copy(self, source: Path, destination: Path) -> None:
        """파일 또는 디렉터리를 복사한다.

        Args:
            self: 이 저장소.
            source: 원본 경로.
            destination: 대상 경로.

        Returns:
            None.
        """
        import shutil

        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    def prune_empty_dirs_under(self, root: Path) -> None:
        """root 아래의 빈 디렉터리만 깊은 쪽부터 제거한다. root 자체는 삭제하지 않는다.

        Args:
            self: 이 저장소.
            root: 상위 루트. 존재하지 않거나 디렉터리가 아니면 아무 것도 하지 않는다.

        Returns:
            None.
        """
        try:
            resolved_root = root.resolve()
        except OSError:
            return
        if not resolved_root.is_dir():
            return
        for dirpath, _dirnames, _filenames in os.walk(resolved_root, topdown=False):
            current = Path(dirpath)
            try:
                if current.resolve() == resolved_root:
                    continue
            except OSError:
                continue
            try:
                if not any(current.iterdir()):
                    current.rmdir()
            except OSError:
                pass
