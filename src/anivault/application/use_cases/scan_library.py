"""Scan library use case. Scans directory for media files via FileRepository."""

from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.application.ports.file_repository import FileRepository

_VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".webm", ".ts", ".m2ts")


def make_execute(
    file_repo: FileRepository,
) -> Callable[[ScanInput, object, Event], ScanResult]:
    """Create execute function with FileRepository injected."""

    def execute(
        input_dto: ScanInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> ScanResult:
        """Scan directory for media files. Uses FileRepository.list_files."""
        if cancel_token.is_set():
            return ScanResult(paths=[])
        if callable(progress_callback):
            progress_callback(
                ProgressEvent(
                    stage="scan",
                    current=0,
                    total=0,
                    message="폴더 스캔 중...",
                    percent=0,
                )
            )
        root = Path(input_dto.path)

        def scan_progress(count: int, item_path: str | None) -> None:
            if callable(progress_callback):
                progress_callback(
                    ProgressEvent(
                        stage="scan",
                        current=count,
                        total=0,
                        message=f"스캔 중: {count}개 파일 발견",
                        percent=0,
                        item_path=item_path,
                    )
                )

        paths = file_repo.list_files(
            root,
            extensions=_VIDEO_EXTENSIONS,
            recursive=input_dto.recursive,
            progress_callback=scan_progress,
        )
        if cancel_token.is_set():
            return ScanResult(paths=[])
        if callable(progress_callback) and paths:
            progress_callback(
                ProgressEvent(
                    stage="scan",
                    current=len(paths),
                    total=len(paths),
                    message=f"스캔 완료: {len(paths)}개 파일",
                    percent=100,
                    item_path=str(paths[-1]) if paths else None,
                )
            )
        return ScanResult(paths=[str(p) for p in paths])

    return execute
