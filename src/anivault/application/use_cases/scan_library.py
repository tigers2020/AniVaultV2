"""scan_library.py

FileRepository로 디렉터리를 스캔해 미디어 파일 경로와 파일명 기준 해상도를 수집한다.

Author: Pom Kim
"""

from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.application.ports.file_repository import FileRepository
from anivault.domain.rules.resolution_from_filename import resolution_from_filename

_VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".webm", ".ts", ".m2ts")


def make_execute(
    file_repo: FileRepository,
) -> Callable[[ScanInput, object, Event], ScanResult]:
    """FileRepository가 주입된 스캔 실행 함수를 만든다.

    Args:
        file_repo: 파일 목록 조회 포트.

    Returns:
        (ScanInput, progress_callback, cancel_token) -> ScanResult 클로저.
    """

    def execute(
        input_dto: ScanInput,
        progress_callback: object,
        cancel_token: Event,
    ) -> ScanResult:
        """디렉터리를 스캔해 비디오 경로와 해상도 라벨을 반환한다.

        Args:
            input_dto: 스캔 루트 경로·재귀 여부.
            progress_callback: ProgressEvent를 받는 콜백. 없으면 무시.
            cancel_token: 설정 시 빈 결과로 조기 반환.

        Returns:
            paths와 resolutions는 동일 길이·순서.
        """
        if cancel_token.is_set():
            return ScanResult(paths=[], resolutions=[])
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
            """list_files 진행 콜백을 ProgressEvent로 넘긴다.

            Args:
                count: 현재까지 발견한 파일 수.
                item_path: 마지막 처리 항목 경로(선택).

            Returns:
                None.
            """
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
            sort=input_dto.sort_paths,
        )
        if cancel_token.is_set():
            return ScanResult(paths=[], resolutions=[])
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
        str_paths = [str(p) for p in paths]
        resolutions = [resolution_from_filename(p) for p in str_paths]
        return ScanResult(paths=str_paths, resolutions=resolutions)

    return execute
