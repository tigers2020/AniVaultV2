"""scan_library.py

FileRepository로 디렉터리를 스캔해 미디어 파일 경로와 파일명 기준 해상도를 수집한다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import nullcontext
from functools import partial
from pathlib import Path
from threading import Event
from typing import cast

from anivault.application.ports.file_repository import FileRepository
from anivault.application.ports.library_index_port import (
    LibraryIndexRepository,
    ScanSessionStatus,
)
from anivault.application.ports.parse_cache_port import ParseCacheRepository
from anivault.application.ports.video_stream_resolution_port import VideoStreamResolutionPort
from anivault.constants.application.statuses import (
    SCAN_SESSION_STATUS_CANCELLED,
    SCAN_SESSION_STATUS_FAILED,
    SCAN_SESSION_STATUS_SUCCESS,
)
from anivault.contracts.library_index import BulkMediaUpsertItem, IndexedMediaForParse
from anivault.contracts.progress import ProgressEvent
from anivault.contracts.scan import ScanInput, ScanResult
from anivault.domain.media.extensions import VIDEO_SCAN_EXTENSIONS, classify_media_kind
from anivault.domain.rules.resolution_from_filename import resolution_from_filename
from anivault.domain.services.subtitle_scan_filter import filter_subtitle_paths_without_paired_video

logger = logging.getLogger(__name__)

SCAN_STATUS_CANCELLED: ScanSessionStatus = cast(ScanSessionStatus, SCAN_SESSION_STATUS_CANCELLED)
SCAN_STATUS_SUCCESS: ScanSessionStatus = cast(ScanSessionStatus, SCAN_SESSION_STATUS_SUCCESS)
SCAN_STATUS_FAILED: ScanSessionStatus = cast(ScanSessionStatus, SCAN_SESSION_STATUS_FAILED)


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
        bulk_items: list[BulkMediaUpsertItem] = []
        for p in paths:
            if cancel_token.is_set():
                assert scan_id is not None
                library_index.finish_scan(
                    scan_id,
                    status=SCAN_STATUS_CANCELLED,
                    files_seen=len(seen),
                    files_added=files_added,
                    files_updated=files_updated,
                    files_removed=0,
                )
                return root_id
            ap = str(p)
            bulk_items.append(
                BulkMediaUpsertItem(
                    absolute_path=ap,
                    media_kind=classify_media_kind(ap),
                )
            )

        if bulk_items:
            bulk_result = library_index.upsert_media_files(root_id, scan_id, bulk_items)
            files_added = bulk_result.files_added
            files_updated = bulk_result.files_updated
            seen = set(bulk_result.seen_path_norms)
        assert scan_id is not None
        removed = library_index.mark_missing_deleted(root_id, scan_id, seen)
        library_index.finish_scan(
            scan_id,
            status=SCAN_STATUS_SUCCESS,
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
                    status=SCAN_STATUS_FAILED,
                    files_seen=len(seen),
                    files_added=files_added,
                    files_updated=files_updated,
                    files_removed=0,
                    error_message=str(e),
                )
            except Exception:
                logger.exception("scan_sessions 종료 기록 실패")
        return None


def _notify_progress(progress_callback: object, event: ProgressEvent) -> None:
    """progress_callback이 호출 가능하면 ProgressEvent를 넘긴다.

    Args:
        progress_callback: ProgressEvent 소비자. callable이 아니면 무시.
        event: 진행 상태 이벤트.

    Returns:
        None.
    """
    if not callable(progress_callback):
        return
    cast(Callable[[ProgressEvent], None], progress_callback)(event)


def _make_scan_list_progress_callback(
    progress_callback: object,
) -> Callable[[int, str | None], None]:
    """file_repo.list_files용 진행 콜백을 만든다.

    Args:
        progress_callback: ProgressEvent 소비자.

    Returns:
        (count, item_path)를 받아 진행을 보고하는 콜백.
    """

    def scan_progress(count: int, item_path: str | None) -> None:
        """list_files 진행을 ProgressEvent로 변환한다.

        Args:
            count: 현재까지 발견한 파일 수.
            item_path: 마지막 처리 항목 경로(선택).

        Returns:
            None.
        """
        _notify_progress(
            progress_callback,
            ProgressEvent(
                stage="scan",
                current=count,
                total=0,
                message=f"스캔 중: {count}개 파일 발견",
                percent=0,
                item_path=item_path,
            ),
        )

    return scan_progress


def _persist_index_and_resolve(
    library_index: LibraryIndexRepository | None,
    *,
    scan_root_str: str,
    paths: list[Path],
    str_paths: list[str],
    cancel_token: Event,
) -> tuple[int | None, list[IndexedMediaForParse | None] | None]:
    """라이브러리 인덱스에 스캔을 반영하고 파싱용 메타를 resolve한다.

    Args:
        library_index: 인덱스 저장소. None이면 반영·resolve 생략.
        scan_root_str: 스캔 루트 경로 문자열.
        paths: 스캔된 Path 목록.
        str_paths: 동일 항목의 절대 경로 문자열 목록.
        cancel_token: 인덱싱 중 취소 시 부분 결과만 반영될 수 있음.

    Returns:
        (index_root_id, resolved). library_index가 None이면 (None, None).
    """
    if library_index is None:
        return None, None
    index_root_id = _try_persist_library_index(
        library_index,
        scan_root_str=scan_root_str,
        paths=paths,
        cancel_token=cancel_token,
    )
    if index_root_id is None:
        return None, None
    resolve_media = getattr(library_index, "resolve_media_for_parse", None)
    if not callable(resolve_media):
        return index_root_id, None
    resolved = resolve_media(index_root_id, str_paths)
    return index_root_id, cast(list[IndexedMediaForParse | None], resolved)


def _resolve_resolution_for_scanned_path(
    path_str: str,
    media_meta: IndexedMediaForParse | None,
    parse_cache: ParseCacheRepository | None,
    resolution_probe: VideoStreamResolutionPort | None,
) -> tuple[str, str, str | None]:
    """단일 경로에 대한 표시 해상도와 출처·캐시 서명을 계산한다.

    Args:
        path_str: 절대 경로 문자열.
        media_meta: 인덱스에서 resolve된 메타. 없으면 캐시 조회 생략.
        parse_cache: 해상도 캐시. None이면 조회 생략.
        resolution_probe: 파일명으로 알 수 없을 때 ffprobe 등 후보.

    Returns:
        (resolution, source, signature). 미검출 시 resolution은 빈 문자열. signature는 캐시 upsert용.
    """
    signature: str | None = None
    if media_meta is not None:
        signature = _resolution_signature(media_meta.size_bytes, media_meta.mtime_ns)
    if parse_cache is not None and media_meta is not None and signature is not None:
        cached = parse_cache.get_valid_resolution(media_meta.id, signature)
        if cached:
            return cached, "cache", signature
    res = resolution_from_filename(path_str)
    if res:
        return res, "filename", signature
    if resolution_probe is not None and classify_media_kind(path_str) == "video":
        return resolution_probe.probe_display_resolution(path_str), "ffprobe", signature
    return "", "filename", signature


def _maybe_write_resolution_to_parse_cache(
    parse_cache: ParseCacheRepository | None,
    media_meta: IndexedMediaForParse | None,
    signature: str | None,
    res: str,
    source: str,
) -> None:
    """캐시 miss 후 얻은 해상도를 parse_cache에 기록한다.

    Args:
        parse_cache: 해상도 캐시.
        media_meta: media_files id 등.
        signature: 무효화 서명.
        res: 확정 해상도 문자열.
        source: cache | filename | ffprobe.

    Returns:
        None.
    """
    if parse_cache is None or media_meta is None or signature is None:
        return
    if not res or source == "cache":
        return
    parse_cache.upsert_resolution(
        media_file_id=media_meta.id,
        signature=signature,
        value=res,
        source=source,
    )


def _emit_resolution_row_progress(
    progress_callback: object,
    *,
    row_index: int,
    total: int,
    path_str: str,
) -> None:
    """해상도 처리 루프 한 행에 대한 진행 이벤트를 보낸다.

    Args:
        progress_callback: ProgressEvent 소비자.
        row_index: 0 기반 행 인덱스.
        total: 전체 행 수.
        path_str: 현재 파일 경로.

    Returns:
        None.
    """
    if not callable(progress_callback) or total <= 0:
        return
    _notify_progress(
        progress_callback,
        ProgressEvent(
            stage="scan",
            current=row_index + 1,
            total=total,
            message=f"해상도 확인 중 ({row_index + 1}/{total})",
            percent=int((row_index + 1) * 100 / total),
            item_path=path_str,
        ),
    )


def _collect_resolutions_after_scan(
    str_paths: list[str],
    resolved: list[IndexedMediaForParse | None] | None,
    parse_cache: ParseCacheRepository | None,
    resolution_probe: VideoStreamResolutionPort | None,
    progress_callback: object,
    cancel_token: Event,
) -> list[str] | None:
    """배치 컨텍스트 안에서 경로별 해상도를 수집한다.

    Args:
        str_paths: 절대 경로 문자열 목록.
        resolved: 인덱스 resolve 결과(경로 순서대로). None이면 메타 없음.
        parse_cache: 해상도 캐시.
        resolution_probe: 파일명 미검출 시 메타 조회 포트.
        progress_callback: ProgressEvent 소비자.
        cancel_token: 설정 시 수집 중단하고 None 반환.

    Returns:
        resolutions. 취소 시 None.
    """
    resolutions: list[str] = []
    res_batch_cm = (
        parse_cache.resolution_write_batch() if parse_cache is not None else nullcontext()
    )
    with res_batch_cm:
        total_paths = len(str_paths)
        for i, p in enumerate(str_paths):
            if cancel_token.is_set():
                return None
            media_meta = resolved[i] if resolved is not None and i < len(resolved) else None
            res, source, signature = _resolve_resolution_for_scanned_path(
                p,
                media_meta,
                parse_cache,
                resolution_probe,
            )
            resolutions.append(res)
            _maybe_write_resolution_to_parse_cache(
                parse_cache,
                media_meta,
                signature,
                res,
                source,
            )
            _emit_resolution_row_progress(
                progress_callback,
                row_index=i,
                total=total_paths,
                path_str=p,
            )
    return resolutions


def _execute_scan(
    file_repo: FileRepository,
    extensions: tuple[str, ...],
    library_index: LibraryIndexRepository | None,
    parse_cache: ParseCacheRepository | None,
    resolution_probe: VideoStreamResolutionPort | None,
    input_dto: ScanInput,
    progress_callback: object,
    cancel_token: Event,
) -> ScanResult:
    """스캔·인덱스·해상도 수집을 한 번에 수행한다.

    Args:
        file_repo: 파일 나열 포트.
        extensions: 스캔 확장자 집합.
        library_index: 선택 라이브러리 인덱스.
        parse_cache: 선택 파싱/해상도 캐시.
        resolution_probe: 선택 비디오 해상도 프로브.
        input_dto: 스캔 입력 DTO.
        progress_callback: 진행 콜백.
        cancel_token: 취소 토큰.

    Returns:
        ScanResult.
    """
    if cancel_token.is_set():
        return ScanResult(paths=[], resolutions=[])
    _notify_progress(
        progress_callback,
        ProgressEvent(
            stage="scan",
            current=0,
            total=0,
            message="폴더 스캔 중...",
            percent=0,
        ),
    )
    root = Path(input_dto.path)
    paths = file_repo.list_files(
        root,
        extensions=extensions,
        recursive=input_dto.recursive,
        progress_callback=_make_scan_list_progress_callback(progress_callback),
        sort=input_dto.sort_paths,
    )
    if cancel_token.is_set():
        return ScanResult(paths=[], resolutions=[])
    if paths:
        _notify_progress(
            progress_callback,
            ProgressEvent(
                stage="scan",
                current=len(paths),
                total=len(paths),
                message=f"스캔 완료: {len(paths)}개 파일",
                percent=100,
                item_path=str(paths[-1]) if paths else None,
            ),
        )
    if input_dto.exclude_subtitles_with_paired_video:
        paths = filter_subtitle_paths_without_paired_video(paths)
    str_paths = [str(p) for p in paths]
    index_root_id, resolved = _persist_index_and_resolve(
        library_index,
        scan_root_str=input_dto.path,
        paths=paths,
        str_paths=str_paths,
        cancel_token=cancel_token,
    )
    resolutions = _collect_resolutions_after_scan(
        str_paths,
        resolved,
        parse_cache,
        resolution_probe,
        progress_callback,
        cancel_token,
    )
    if resolutions is None:
        return ScanResult(paths=[], resolutions=[])
    return ScanResult(
        paths=str_paths,
        resolutions=resolutions,
        index_root_id=index_root_id,
    )


def make_execute(
    file_repo: FileRepository,
    *,
    extensions: tuple[str, ...] = VIDEO_SCAN_EXTENSIONS,
    library_index: LibraryIndexRepository | None = None,
    parse_cache: ParseCacheRepository | None = None,
    resolution_probe: VideoStreamResolutionPort | None = None,
) -> Callable[[ScanInput, object, Event], ScanResult]:
    """FileRepository가 주입된 스캔 실행 함수를 만든다.

    Args:
        file_repo: 파일 목록 조회 포트.
        extensions: 수집할 파일 확장자(점 포함, 소문자 권장). 기본은 비디오 집합.
        library_index: 주입 시 스캔 후 `media_files` 등에 반영한다.
        parse_cache: 주입 시 해상도 캐시를 조회/저장한다.
        resolution_probe: 파일명 미검출 시 비디오 메타 해상도 조회 포트.

    Returns:
        (ScanInput, progress_callback, cancel_token) -> ScanResult 클로저.
    """
    return cast(
        Callable[[ScanInput, object, Event], ScanResult],
        partial(
            _execute_scan,
            file_repo,
            extensions,
            library_index,
            parse_cache,
            resolution_probe,
        ),
    )


def _resolution_signature(size_bytes: int, mtime_ns: int) -> str:
    """해상도 캐시 무효화에 사용할 서명을 만든다.

    Args:
        size_bytes: 파일 크기(byte).
        mtime_ns: 수정 시각(ns).

    Returns:
        size/mtime 기반 서명 문자열.
    """
    return f"res-v1:{size_bytes}:{mtime_ns}"
