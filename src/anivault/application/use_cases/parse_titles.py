"""parse_titles.py

FilenameParser로 각 경로의 파일명을 파싱해 제목·시즌·연도·해상도를 채운다.

Author: Pom Kim
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from threading import Event

from anivault.application.dto.library_index import IndexedMediaForParse
from anivault.application.dto.parse import ParsedInfo, ParseInput, ParseResult
from anivault.application.dto.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.application.dto.parse_serde import parsed_info_to_compact_json
from anivault.application.dto.progress import ProgressEvent
from anivault.application.ports.filename_parser import FilenameParser
from anivault.application.ports.library_index_port import LibraryIndexRepository
from anivault.application.ports.parse_cache_port import ParseCacheRepository
from anivault.domain.parsing.normalize_cache_title import normalize_title_for_parse_cache
from anivault.domain.parsing.parse_signature import compute_parse_input_signature
from anivault.domain.parsing.parser_version import PARSER_VERSION
from anivault.domain.rules.anime_title_refine import apply_anime_title_refine
from anivault.domain.rules.parent_folder_title import augment_parsed_info_with_parent_folder

logger = logging.getLogger(__name__)


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


def make_execute(
    parser: FilenameParser,
    *,
    library_index: LibraryIndexRepository | None = None,
    parse_cache: ParseCacheRepository | None = None,
) -> Callable[[ParseInput, object, Event], ParseResult]:
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
        progress_callback: object,
        cancel_token: Event,
    ) -> ParseResult:
        """경로 순서대로 파일명을 파싱한 ParsedInfo 목록을 반환한다.

        Args:
            input_dto: 파싱할 경로 목록·선택 인덱스 루트 ID.
            progress_callback: ProgressEvent를 받는 콜백. 없으면 무시.
            cancel_token: 설정 시 지금까지 파싱분만 반환.

        Returns:
            입력 순서와 동일한 parsed 리스트.
        """
        paths = input_dto.paths or []
        if cancel_token.is_set():
            return ParseResult(parsed=[])
        total = len(paths)
        index_root_id = input_dto.index_root_id
        use_cache = (
            index_root_id is not None and library_index is not None and parse_cache is not None
        )
        resolved: list[IndexedMediaForParse | None] | None = None
        if use_cache:
            assert library_index is not None
            assert parse_cache is not None
            assert index_root_id is not None
            resolved = library_index.resolve_media_for_parse(index_root_id, paths)
        signatures: list[str | None] = [None] * total
        cached_by_media_id: dict[int, ParsedInfo] = {}
        if use_cache and resolved is not None and parse_cache is not None:
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
        if callable(progress_callback) and total:
            progress_callback(
                ProgressEvent(
                    stage="parse",
                    current=0,
                    total=total,
                    message="파싱 캐시 확인 중..." if use_cache else "파일명 파싱 중...",
                    percent=0,
                )
            )
        parsed: list[ParsedInfo] = []
        cache_hits: list[bool] = []
        pending_ok: list[ParseCacheOkWrite] = []
        pending_errors: list[ParseCacheErrorWrite] = []

        def flush_pending_cache_writes() -> None:
            if not use_cache or parse_cache is None:
                return
            if pending_ok:
                parse_cache.upsert_parse_ok_many(pending_ok)
                pending_ok.clear()
            if pending_errors:
                parse_cache.upsert_parse_error_many(pending_errors)
                pending_errors.clear()

        for i, path in enumerate(paths):
            if cancel_token.is_set():
                flush_pending_cache_writes()
                return ParseResult(parsed=parsed, cache_hits=cache_hits)
            meta = None
            if use_cache and resolved is not None:
                meta = resolved[i]
            signature: str | None = signatures[i] if i < len(signatures) else None
            cached: ParsedInfo | None = None
            if use_cache and parse_cache is not None and meta is not None and signature is not None:
                cached = cached_by_media_id.get(meta.id)
            if cached is not None:
                parsed.append(cached)
                cache_hits.append(True)
            else:
                name = Path(path).name
                stem = Path(path).stem
                try:
                    info = parser.parse(name)
                except Exception as e:
                    logger.exception("파일명 파싱 실패 path=%s: %s", path, e)
                    if (
                        use_cache
                        and parse_cache is not None
                        and meta is not None
                        and signature is not None
                    ):
                        pending_errors.append(
                            ParseCacheErrorWrite(
                                media_file_id=meta.id,
                                parser_version=PARSER_VERSION,
                                parse_input_signature=signature,
                                error_code=type(e).__name__,
                                error_message=str(e),
                            )
                        )
                    parsed.append(ParsedInfo())
                    cache_hits.append(False)
                else:
                    info = apply_anime_title_refine(stem, info)
                    info = augment_parsed_info_with_parent_folder(path, info)
                    parsed.append(info)
                    cache_hits.append(False)
                    if (
                        use_cache
                        and parse_cache is not None
                        and meta is not None
                        and signature is not None
                    ):
                        dto_json = parsed_info_to_compact_json(info)
                        pending_ok.append(
                            ParseCacheOkWrite(
                                media_file_id=meta.id,
                                parser_version=PARSER_VERSION,
                                parse_input_signature=signature,
                                parsed=info,
                                dto_json=dto_json,
                                parsed_title=info.title or None,
                                parsed_title_normalized=normalize_title_for_parse_cache(
                                    info.title,
                                ),
                                parsed_year=_optional_int_from_str(info.year),
                                season_number=_optional_int_from_str(info.season),
                                episode_start=_optional_int_from_str(info.episode),
                                episode_end=None,
                                episode_count=None,
                                confidence=None,
                            )
                        )
            if callable(progress_callback) and total:
                pct = int((i + 1) * 100 / total) if total else 100
                progress_callback(
                    ProgressEvent(
                        stage="parse",
                        current=i + 1,
                        total=total,
                        message=(
                            f"파싱 캐시 로딩 중 {i + 1}/{total}"
                            if cached is not None
                            else f"파싱 중 {i + 1}/{total}"
                        ),
                        percent=pct,
                        item_path=path,
                    )
                )
        flush_pending_cache_writes()
        return ParseResult(parsed=parsed, cache_hits=cache_hits)

    return execute
