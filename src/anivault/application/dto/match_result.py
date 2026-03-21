"""match_result.py

match_series 유스케이스 입·출력 DTO.

Author: Pom Kim
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class MatchFileRow:
    """매칭용 파일 한 줄 스냅샷(GUI 타입 없음)."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    tmdb_series_id: str
    tmdb_poster_path: str
    tmdb_backdrop_path: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    backdrop_url: str
    target_path: str


@dataclass(slots=True)
class GroupMatchResultDTO:
    """그룹별 매칭 결과(디버깅·향후 UI)."""

    group_key: str
    matched: bool
    tmdb_id: int | None
    korean_group_title: str
    original_title: str
    confidence: float
    reason: str


@dataclass(slots=True)
class MatchInput:
    """match_series 입력. 파일당 한 행, 파이프라인 순서."""

    files: tuple[MatchFileRow, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class MatchResult:
    """TMDB 매칭 후 갱신된 파일 행. 순서 유지."""

    files: tuple[MatchFileRow, ...]
    groups: tuple[GroupMatchResultDTO, ...] = field(default_factory=tuple)
