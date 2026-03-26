"""caching_metadata_provider.py

TitleMatchRepository 검색 캐시를 앞에 두는 MetadataProvider 래퍼.

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
from anivault.domain.rules.tmdb_search_cache_key import build_tmdb_search_cache_key
from anivault.domain.rules.tmdb_search_query import normalize_tmdb_search_query

logger = logging.getLogger(__name__)

_SEARCH_TTL_OK_DAYS = 7
_SEARCH_TTL_EMPTY_DAYS = 1


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
        self._language = (language or "").strip() or "und"

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
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                logger.warning("tmdb 검색 캐시 JSON 무효 key=%s: %s", key, e)
        candidates = list(self._inner.search_series(query, year=year))
        days = _SEARCH_TTL_OK_DAYS if candidates else _SEARCH_TTL_EMPTY_DAYS
        expires = utc_plus_days_sqlite_text(days)
        payload = _encode_candidates_json(candidates)
        nq = normalize_tmdb_search_query(query)
        try:
            self._title_match.put_search_cache(
                key,
                language=self._language,
                normalized_query=nq,
                year_hint=year,
                page=1,
                response_json=payload,
                expires_at=expires,
            )
        except Exception:
            logger.exception("tmdb_search_cache 기록 실패 key=%s", key)
        return candidates


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
