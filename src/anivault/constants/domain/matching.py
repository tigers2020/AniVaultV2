"""Domain/application matching constants."""

from __future__ import annotations

from typing import Final

TMDB_MAX_CANDIDATES: Final[int] = 5

MATCH_REASON_EXACT_NAME: Final[str] = "exact_name"
MATCH_REASON_PARTIAL_NAME: Final[str] = "partial_name"
MATCH_REASON_FALLBACK_FIRST: Final[str] = "fallback_first"
MATCH_REASON_FIRST_RESULT: Final[str] = "first_result"
MATCH_REASON_NO_RESULTS: Final[str] = "no_results"
MATCH_REASON_CANCELLED: Final[str] = "cancelled"

MATCH_SCORE_EXACT_NAME: Final[float] = 10.0
MATCH_SCORE_PARTIAL_NAME: Final[float] = 5.0
MATCH_SCORE_LOCALIZED_NAME_BONUS: Final[float] = 2.0
MATCH_SCORE_YEAR_BONUS: Final[float] = 3.0
MATCH_SCORE_POPULARITY_MULTIPLIER: Final[float] = 0.01
MATCH_SCORE_NORMALIZER: Final[float] = 15.0
MATCH_CONFIDENCE_FALLBACK: Final[float] = 0.5

TMDB_SERIES_CACHE_TTL_DAYS: Final[int] = 7
