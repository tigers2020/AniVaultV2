"""Title match repository contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MatchStatus = Literal["auto_matched", "confirmed", "rejected"]


@dataclass(frozen=True, slots=True)
class GroupTmdbMatchRecord:
    """Stored TMDB match for a title group."""

    group_id: int
    tmdb_id: int
    match_status: MatchStatus
    match_score: float | None
