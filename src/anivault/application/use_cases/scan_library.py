"""scan_library.py

FileRepository로 디렉터리를 스캔해 미디어 파일 경로와 파일명 기준 해상도를 수집한다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.scan import ScanInput, ScanResult
from anivault.application.ports.file_repository import FileRepository
from anivault.application.ports.library_index_port import LibraryIndexRepository
from anivault.domain.media.extensions import VIDEO_SCAN_EXTENSIONS, classify_media_kind
from anivault.domain.path_norm import normalize_path_key
from anivault.domain.rules.resolution_from_filename import resolution_from_filename

logger = logging.getLogger(__name__)


def _try_persist_library_index(
    library_index: LibraryIndexRepository,
    *,
    scan_root_str: str,
    paths: list[Path],
    cancel_token: Event,
) -> int | None:
    """스캔 목록을 `LibraryIndexRepository`에 반영한다. 실패는 로그만(옵션 A).

    성공·취소(부분 반영) 시 `library_roots.id`를 반환해 파싱 캐시가 동일 루트로 resolve 할 수 있게 한다.
    예외로 중단되면 None.

    Args:
        library_index: 인덱스 저장소.
        scan_root_str: 스캔 루트 경로 문자열.
        paths: 스캔된 `Path` 목록(빈 목록 허용).
        cancel_token: 설정 시 인덱싱 중단 후 세션 `cancelled`.

    Returns:
        반영에 사용한 루트 ID. 치명적 실패 시 None.
    """
    scan_id: int | None = None
    files_added = 0
    files_updated = 0
    seen: set[str] = set()
    files_seen = len(paths)
    root_id: int | None = None
    try:
        root_id = library_index.upsert_root(scan_root_str)
        scan_id = library_index.begin_scan(root_id, "full")
        for p in paths:
            if cancel_token.is_set():
                assert scan_id is not None
                library_index.finish_scan(
                    scan_id,
                    status="cancelled",
                    files_seen=len(seen),
                    files_added=files_added,
                    files_updated=files_updated,
                    files_removed=0,
                )
                return root_id
            ap = str(p)
            kind = classify_media_kind(ap)
            a, u = library_index.upsert_media_file(
                root_id,
                scan_id,
                absolute_path=ap,
                media_kind=kind,
            )
            files_added += int(a)
            files_updated += int(u)
            seen.add(normalize_path_key(ap))
        assert scan_id is not None
        removed = library_index.mark_missing_deleted(root_id, scan_id, seen)
        library_index.finish_scan(
            scan_id,
            status="success",
            files_seen=files_seen,
            files_added=files_added,
            files_updated=files_updated,
            files_removed=removed,
        )
        return root_id
    except Exception as e:
        logger.exception("라이브러리 인덱스 반영 실패: %s", e)
        if scan_id is not None:
            try:
                library_index.finish_scan(
                    scan_id,
                    status="failed",
                    files_seen=len(seen),
                    files_added=files_added,
                    files_updated=files_updated,
                    files_removed=0,
                    error_message=str(e),
                )
            except Exception:
                logger.exception("scan_sessions 종료 기록 실패")
        return None


def make_execute(
    file_repo: FileRepository,
    *,
    extensions: tuple[str, ...] = VIDEO_SCAN_EXTENSIONS,
    library_index: LibraryIndexRepository | None = None,
) -> Callable[[ScanInput, object, Event], ScanResult]:
    """FileRepository가 주입된 스캔 실행 함수를 만든다.

    Args:
        file_repo: 파일 목록 조회 포트.
        extensions: 수집할 파일 확장자(점 포함, 소문자 권장). 기본은 비디오 집합.
        library_index: 주입 시 스캔 후 `media_files` 등에 반영한다.

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
            extensions=extensions,
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
        index_root_id: int | None = None
        if library_index is not None:
            index_root_id = _try_persist_library_index(
                library_index,
                scan_root_str=input_dto.path,
                paths=paths,
                cancel_token=cancel_token,
            )
        return ScanResult(
            paths=str_paths,
            resolutions=resolutions,
            index_root_id=index_root_id,
        )

    return execute
