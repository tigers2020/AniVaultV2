"""parse_titles.py

FilenameParser로 각 경로의 파일명을 파싱해 제목·시즌·연도·해상도를 채운다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.ports.filename_parser import FilenameParser
from anivault.application.ports.library_index_port import LibraryIndexRepository
from anivault.application.ports.parse_cache_port import ParseCacheRepository
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX, PROGRESS_STAGE_PARSE
from anivault.contracts.library_index import IndexedMediaForParse
from anivault.contracts.parse import ParseInput, ParseResult
from anivault.contracts.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.contracts.progress import ProgressEvent
from anivault.domain.models import ParsedInfo
from anivault.domain.models.parsed_info_serde import parsed_info_to_compact_json
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parse_signature import compute_parse_input_signature
from anivault.domain.parsing.parser_version import PARSER_VERSION
from anivault.domain.rules.anime_title_refine import apply_anime_title_refine
from anivault.domain.rules.parent_folder_title import augment_parsed_info_with_parent_folder

logger = logging.getLogger(__name__)
type ProgressCallback = Callable[[ProgressEvent], None]


def _optional_int_from_str(s: str) -> int | None:
    """숫자만 있는 문자열을 int로 바꾼다.

    Args:
        s: 시즌·에피소드 등.

    Returns:
        파싱 성공 시 int. 빈 문자열·비숫자면 None.
    """
    t = (s or "").strip()
    if not t:
        return None
    try:
        return int(t)
    except ValueError:
        return None


def _episode_bounds(info: ParsedInfo) -> tuple[int | None, int | None, int | None]:
    """Compute parse-cache summary fields from normalized episode numbers."""
    if info.episode_numbers:
        return info.episode_numbers[0], info.episode_numbers[-1], len(info.episode_numbers)
    one = _optional_int_from_str(info.episode)
    if one is None:
        return None, None, None
    return one, one, 1


def _as_progress_callback(progress_callback: object) -> ProgressCallback | None:
    """호출 가능한 진행률 콜백만 좁혀서 반환한다."""
    if not callable(progress_callback):
        return None
    return progress_callback if callable(progress_callback) else None


def _build_cache_state(
    *,
    paths: list[str],
    use_cache: bool,
    index_root_id: int | None,
    library_index: LibraryIndexRepository | None,
    parse_cache: ParseCacheRepository | None,
) -> tuple[list[IndexedMediaForParse | None] | None, list[str | None], dict[int, ParsedInfo]]:
    """캐시 조회에 필요한 메타/서명/히트 맵을 준비한다."""
    total = len(paths)
    signatures: list[str | None] = [None] * total
    if not use_cache or library_index is None or parse_cache is None or index_root_id is None:
        return None, signatures, {}

    resolved = library_index.resolve_media_for_parse(index_root_id, paths)
    lookups: list[ParseCacheLookup] = []
    for i, meta in enumerate(resolved):
        if meta is None:
            continue
        lookup_signature = compute_parse_input_signature(
            meta.path_norm,
            meta.size_bytes,
            meta.mtime_ns,
        )
        signatures[i] = lookup_signature
        lookups.append(ParseCacheLookup(meta.id, lookup_signature))
    cached_by_media_id = parse_cache.get_valid_parses(lookups)
    return resolved, signatures, cached_by_media_id


def _emit_initial_progress(
    callback: ProgressCallback | None,
    *,
    total: int,
    use_cache: bool,
) -> None:
    """파싱 시작 시 0% 이벤트를 보낸다."""
    if callback is None or total == 0:
        return
    callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_PARSE,
            current=0,
            total=total,
            message="파싱 캐시 확인 중..." if use_cache else "파일명 파싱 중...",
            percent=0,
        )
    )


def _emit_item_progress(
    callback: ProgressCallback | None,
    *,
    index: int,
    total: int,
    path: str,
    cached: bool,
) -> None:
    """항목 처리 후 진행률 이벤트를 보낸다."""
    if callback is None or total == 0:
        return
    pct = int((index + 1) * PROGRESS_PERCENT_MAX / total)
    callback(
        ProgressEvent(
            stage=PROGRESS_STAGE_PARSE,
            current=index + 1,
            total=total,
            message=(
                f"파싱 캐시 로딩 중 {index + 1}/{total}"
                if cached
                else f"파싱 중 {index + 1}/{total}"
            ),
            percent=pct,
            item_path=path,
        )
    )


def _flush_pending_cache_writes(
    *,
    use_cache: bool,
    parse_cache: ParseCacheRepository | None,
    pending_ok: list[ParseCacheOkWrite],
    pending_errors: list[ParseCacheErrorWrite],
) -> None:
    """누적된 캐시 write 배치를 DB에 반영한다."""
    if not use_cache or parse_cache is None:
        return
    if pending_ok:
        parse_cache.upsert_parse_ok_many(pending_ok)
        pending_ok.clear()
    if pending_errors:
        parse_cache.upsert_parse_error_many(pending_errors)
        pending_errors.clear()


def _build_ok_write(
    *,
    media_file_id: int,
    signature: str,
    info: ParsedInfo,
) -> ParseCacheOkWrite:
    """정상 파싱 결과를 캐시 write DTO로 변환한다."""
    dto_json = parsed_info_to_compact_json(info)
    episode_start, episode_end, episode_count = _episode_bounds(info)
    return ParseCacheOkWrite(
        media_file_id=media_file_id,
        parser_version=PARSER_VERSION,
        parse_input_signature=signature,
        parsed=info,
        dto_json=dto_json,
        parsed_title=info.title or None,
        parsed_title_normalized=normalize_title_for_parse_cache(info.title),
        parsed_year=_optional_int_from_str(info.year),
        season_number=_optional_int_from_str(info.season),
        episode_start=episode_start,
        episode_end=episode_end,
        episode_count=episode_count,
        confidence=None,
    )


def _resolve_one_path(
    *,
    path: str,
    parser: FilenameParser,
    use_cache: bool,
    parse_cache: ParseCacheRepository | None,
    meta: IndexedMediaForParse | None,
    signature: str | None,
    cached_by_media_id: dict[int, ParsedInfo],
) -> tuple[ParsedInfo, bool, ParseCacheOkWrite | None, ParseCacheErrorWrite | None]:
    """단일 경로를 캐시 또는 파싱으로 해석하고 write DTO를 반환한다."""
    if use_cache and parse_cache is not None and meta is not None and signature is not None:
        cached = cached_by_media_id.get(meta.id)
        if cached is not None:
            return cached, True, None, None

    name = Path(path).name
    stem = Path(path).stem
    try:
        info = parser.parse(name)
    except Exception as e:
        logger.exception("파일명 파싱 실패 path=%s: %s", path, e)
        error_write = None
        if use_cache and parse_cache is not None and meta is not None and signature is not None:
            error_write = ParseCacheErrorWrite(
                media_file_id=meta.id,
                parser_version=PARSER_VERSION,
                parse_input_signature=signature,
                error_code=type(e).__name__,
                error_message=str(e),
            )
        return ParsedInfo(), False, None, error_write

    refined = apply_anime_title_refine(stem, info)
    enriched = augment_parsed_info_with_parent_folder(path, refined)
    ok_write = None
    if use_cache and parse_cache is not None and meta is not None and signature is not None:
        ok_write = _build_ok_write(media_file_id=meta.id, signature=signature, info=enriched)
    return enriched, False, ok_write, None


def _execute_parse_titles(
    *,
    parser: FilenameParser,
    library_index: LibraryIndexRepository | None,
    parse_cache: ParseCacheRepository | None,
    input_dto: ParseInput,
    progress_callback: ProgressCallback | None,
    cancel_token: Event,
) -> ParseResult:
    """경로 순서대로 파일명을 파싱한 ParsedInfo 목록을 반환한다."""
    paths = input_dto.paths or []
    if cancel_token.is_set():
        return ParseResult(parsed=[])

    total = len(paths)
    index_root_id = input_dto.index_root_id
    use_cache = index_root_id is not None and library_index is not None and parse_cache is not None
    resolved, signatures, cached_by_media_id = _build_cache_state(
        paths=paths,
        use_cache=use_cache,
        index_root_id=index_root_id,
        library_index=library_index,
        parse_cache=parse_cache,
    )
    _emit_initial_progress(progress_callback, total=total, use_cache=use_cache)
    parsed: list[ParsedInfo] = []
    cache_hits: list[bool] = []
    pending_ok: list[ParseCacheOkWrite] = []
    pending_errors: list[ParseCacheErrorWrite] = []

    for i, path in enumerate(paths):
        if cancel_token.is_set():
            _flush_pending_cache_writes(
                use_cache=use_cache,
                parse_cache=parse_cache,
                pending_ok=pending_ok,
                pending_errors=pending_errors,
            )
            return ParseResult(parsed=parsed, cache_hits=cache_hits)
        meta = resolved[i] if (use_cache and resolved is not None) else None
        signature: str | None = signatures[i] if i < len(signatures) else None
        info, cache_hit, ok_write, error_write = _resolve_one_path(
            path=path,
            parser=parser,
            use_cache=use_cache,
            parse_cache=parse_cache,
            meta=meta,
            signature=signature,
            cached_by_media_id=cached_by_media_id,
        )
        parsed.append(info)
        cache_hits.append(cache_hit)
        if ok_write is not None:
            pending_ok.append(ok_write)
        if error_write is not None:
            pending_errors.append(error_write)
        _emit_item_progress(
            progress_callback,
            index=i,
            total=total,
            path=path,
            cached=cache_hit,
        )

    _flush_pending_cache_writes(
        use_cache=use_cache,
        parse_cache=parse_cache,
        pending_ok=pending_ok,
        pending_errors=pending_errors,
    )
    return ParseResult(parsed=parsed, cache_hits=cache_hits)


def make_execute(
    parser: FilenameParser,
    *,
    library_index: LibraryIndexRepository | None = None,
    parse_cache: ParseCacheRepository | None = None,
) -> Callable[[ParseInput, ProgressCallback | None, Event], ParseResult]:
    """FilenameParser가 주입된 파싱 실행 함수를 만든다.

    Args:
        parser: 파일명 파싱 포트.
        library_index: 주입 시 경로→미디어 메타 resolve.
        parse_cache: 주입 시 서명 기반 캐시 read/write.

    Returns:
        (ParseInput, progress_callback, cancel_token) -> ParseResult 클로저.
    """

    def execute(
        input_dto: ParseInput,
        progress_callback: ProgressCallback | None,
        cancel_token: Event,
    ) -> ParseResult:
        return _execute_parse_titles(
            parser=parser,
            library_index=library_index,
            parse_cache=parse_cache,
            input_dto=input_dto,
            progress_callback=progress_callback,
            cancel_token=cancel_token,
        )

    return execute
