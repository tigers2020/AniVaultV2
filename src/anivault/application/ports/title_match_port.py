"""title_match_port.py

TMDB 검색 캐시·시리즈 행·그룹 매칭 영속화 포트.

Author: Pom Kim
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from anivault.application.dto.title_match import GroupTmdbMatchRecord, MatchStatusDto
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO


@runtime_checkable
class TitleMatchRepository(Protocol):
    """검색 응답 캐시, 시리즈 스냅샷, 그룹 단위 TMDB 매칭."""

    def get_search_cache_json(self, cache_key: str) -> str | None:
        """미만료 검색 캐시 JSON 문자열을 반환한다.

        Args:
            self: 저장소.
            cache_key: `build_tmdb_search_cache_key` 등으로 만든 키.

        Returns:
            compact JSON. miss·만료·손상 시 None.
        """
        ...

    def put_search_cache(
        self,
        cache_key: str,
        *,
        language: str,
        normalized_query: str,
        year_hint: int | None,
        page: int,
        response_json: str,
        expires_at: str,
    ) -> None:
        """검색 캐시를 덮어쓴다.

        Args:
            self: 저장소.
            cache_key: PRIMARY KEY.
            language: API 언어 코드.
            normalized_query: 정규화된 검색어.
            year_hint: 연도 필터. 없으면 NULL 저장.
            page: 페이지 번호.
            response_json: compact UTF-8 JSON.
            expires_at: UTC 만료 시각 ISO 문자열.

        Returns:
            None.
        """
        ...

    def invalidate_search(self, cache_key: str) -> None:
        """단일 `cache_key` 행을 삭제한다(exact).

        Args:
            self: 저장소.
            cache_key: 완성된 캐시 키.

        Returns:
            None.
        """
        ...

    def upsert_series(
        self,
        candidate: TmdbSeriesCandidateDTO,
        *,
        raw_json: str,
        expires_at: str,
    ) -> None:
        """시리즈 스냅샷을 저장·갱신한다.

        Args:
            self: 저장소.
            candidate: 핫 필드 소스.
            raw_json: compact JSON(`candidate` 전체 등).
            expires_at: UTC 만료 시각.

        Returns:
            None.
        """
        ...

    def get_series_candidate(self, tmdb_id: int) -> TmdbSeriesCandidateDTO | None:
        """미만료 `tmdb_series`에서 후보 DTO를 복원한다.

        Args:
            self: 저장소.
            tmdb_id: TMDB TV id.

        Returns:
            DTO. 만료·없음·역직렬화 실패 시 None.
        """
        ...

    def get_group_match(self, group_id: int) -> GroupTmdbMatchRecord | None:
        """그룹의 저장된 TMDB 매칭을 조회한다.

        Args:
            self: 저장소.
            group_id: title_groups.id.

        Returns:
            레코드. 없으면 None.
        """
        ...

    def set_group_match(
        self,
        group_id: int,
        tmdb_id: int,
        match_status: MatchStatusDto,
        match_score: float | None,
    ) -> None:
        """그룹 매칭을 저장하고 `title_groups.tmdb_series_id`를 같이 맞춘다.

        Args:
            self: 저장소.
            group_id: title_groups.id.
            tmdb_id: TMDB 시리즈 id(`tmdb_series`에 행이 있어야 FK 만족).
            match_status: auto_matched / confirmed / rejected.
            match_score: 점수. None 허용.

        Returns:
            None.
        """
        ...

    def invalidate_group_match(self, group_id: int) -> None:
        """그룹 매칭 행을 지우고 `title_groups.tmdb_series_id`를 NULL로 한다.

        Args:
            self: 저장소.
            group_id: title_groups.id.

        Returns:
            None.
        """
        ...
