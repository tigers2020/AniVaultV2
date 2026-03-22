"""tmdb.py

TMDB 메타데이터 DTO. 어댑터가 채우고 유스케이스는 이 타입만 소비한다.

Author: Pom Kim
"""

from dataclasses import dataclass


@dataclass(slots=True)
class TmdbSearchInput:
    """TMDB 시리즈 검색(수동 매칭 다이얼로그 등) 입력."""

    query: str
    year: int | None = None


@dataclass(slots=True)
class TmdbSeriesCandidateDTO:
    """TV 시리즈 검색 후보 한 건(어댑터가 요청한 현지화 필드)."""

    tmdb_id: int
    name_ko: str
    original_name: str
    first_air_date: str
    original_language: str
    overview: str
    poster_path: str
    backdrop_path: str
    popularity: float
