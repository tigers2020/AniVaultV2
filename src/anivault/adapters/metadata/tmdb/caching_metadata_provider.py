"""caching_metadata_provider.py

TitleMatchRepository 검색 캐시를 앞에 두는 MetadataProvider 래퍼.
캐시 miss 후 내부 공급자(예: `TmdbMetadataProvider`)가 TMDB를 호출하면
bootstrap에서 주입된 경우 `tmdb_search_tv_library`에 검색 결과 행이 영구 저장된다.

Author: Pom Kim
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import asdict

from anivault.adapters.persistence.sqlite.sqlite_time import utc_plus_days_sqlite_text
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.constants.adapters.tmdb import (
    TMDB_LOCAL_CANDIDATE_LIMIT,
    TMDB_SEARCH_CACHE_TTL_EMPTY_DAYS,
    TMDB_SEARCH_CACHE_TTL_OK_DAYS,
    UNKNOWN_TMDB_LANGUAGE,
)
from anivault.domain.rules.tmdb_search_cache_key import build_tmdb_search_cache_key
from anivault.domain.rules.tmdb_search_query import normalize_tmdb_search_query

logger = logging.getLogger(__name__)


class CachingMetadataProvider:
    """내부 MetadataProvider 호출을 `tmdb_search_cache`로 감싼다."""

    def __init__(
        self,
        inner: MetadataProvider,
        title_match: TitleMatchRepository,
        *,
        language: str,
    ) -> None:
        """캐시 저장소·언어를 주입한다.

        Args:
            self: 이 인스턴스.
            inner: 실제 TMDB 공급자.
            title_match: 검색 캐시 포트.
            language: `TmdbApiClient.language` 과 동일한 키 문자열.

        Returns:
            None.
        """
        self._inner = inner
        self._title_match = title_match
        self._language = (language or "").strip() or UNKNOWN_TMDB_LANGUAGE

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        """캐시 hit 시 네트워크 없이 후보를 반환한다.

        Args:
            self: 이 공급자.
            query: 검색어.
            year: 첫 방영 연도 필터.

        Returns:
            후보 시퀀스.
        """
        key = build_tmdb_search_cache_key(self._language, query, year=year, page=1)
        cached = self._title_match.get_search_cache_json(key)
        if cached is not None:
            try:
                decoded = _decode_candidates_json(cached)
                return decoded
            except (KeyError, TypeError, ValueError) as e:
                logger.warning("tmdb 검색 캐시 JSON 무효 key=%s: %s", key, e)
        local_candidates = list(
            self._title_match.find_series_candidates_by_title(
                query,
                limit=TMDB_LOCAL_CANDIDATE_LIMIT,
            ),
        )
        if local_candidates:
            _put_search_cache(
                self._title_match,
                key=key,
                language=self._language,
                query=query,
                year=year,
                candidates=local_candidates,
            )
            return local_candidates
        candidates = list(self._inner.search_series(query, year=year))
        _put_search_cache(
            self._title_match,
            key=key,
            language=self._language,
            query=query,
            year=year,
            candidates=candidates,
        )
        return candidates


def _put_search_cache(
    title_match: TitleMatchRepository,
    *,
    key: str,
    language: str,
    query: str,
    year: int | None,
    candidates: list[TmdbSeriesCandidateDTO],
) -> None:
    """검색 결과를 `tmdb_search_cache`에 저장한다.

    Args:
        title_match: 캐시 저장소.
        key: 캐시 키.
        language: API 언어 코드.
        query: 원본 검색어.
        year: 연도 힌트.
        candidates: 저장할 후보 목록.

    Returns:
        None.
    """
    days = TMDB_SEARCH_CACHE_TTL_OK_DAYS if candidates else TMDB_SEARCH_CACHE_TTL_EMPTY_DAYS
    expires = utc_plus_days_sqlite_text(days)
    payload = _encode_candidates_json(candidates)
    nq = normalize_tmdb_search_query(query)
    try:
        title_match.put_search_cache(
            key,
            language=language,
            normalized_query=nq,
            year_hint=year,
            page=1,
            response_json=payload,
            expires_at=expires,
        )
    except Exception:
        logger.exception("tmdb_search_cache 기록 실패 key=%s", key)


def _encode_candidates_json(candidates: list[TmdbSeriesCandidateDTO]) -> str:
    """후보 목록을 compact JSON 배열로 직렬화한다.

    Args:
        candidates: DTO 목록.

    Returns:
        UTF-8 JSON 텍스트.
    """
    return json.dumps(
        [asdict(c) for c in candidates],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _decode_candidates_json(raw: str) -> list[TmdbSeriesCandidateDTO]:
    """JSON 배열을 후보 목록으로 복원한다.

    Args:
        raw: compact JSON.

    Returns:
        DTO 리스트.

    Raises:
        json.JSONDecodeError: JSON 파싱 실패.
        (KeyError, TypeError, ValueError): 스키마 불일치.
    """
    data = json.loads(raw)
    if not isinstance(data, list):
        msg = "search cache JSON은 배열이어야 한다"
        raise TypeError(msg)
    out: list[TmdbSeriesCandidateDTO] = []
    for item in data:
        if not isinstance(item, dict):
            msg = "각 원소는 객체여야 한다"
            raise TypeError(msg)
        out.append(
            TmdbSeriesCandidateDTO(
                tmdb_id=int(item["tmdb_id"]),
                name_ko=str(item.get("name_ko", "") or ""),
                original_name=str(item.get("original_name", "") or ""),
                first_air_date=str(item.get("first_air_date", "") or ""),
                original_language=str(item.get("original_language", "") or ""),
                overview=str(item.get("overview", "") or ""),
                poster_path=str(item.get("poster_path", "") or ""),
                backdrop_path=str(item.get("backdrop_path", "") or ""),
                popularity=float(item.get("popularity", 0.0) or 0.0),
            ),
        )
    return out
