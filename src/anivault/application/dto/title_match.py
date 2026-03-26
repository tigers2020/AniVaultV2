"""title_match.py

TMDB 매칭 저장소·그룹 매핑 DTO.

Author: Pom Kim
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MatchStatusDto = Literal["auto_matched", "confirmed", "rejected"]


@dataclass(frozen=True, slots=True)
class GroupTmdbMatchRecord:
    """group_tmdb_matches 한 행 조회 결과."""

    group_id: int
    tmdb_id: int
    match_status: MatchStatusDto
    match_score: float | None
