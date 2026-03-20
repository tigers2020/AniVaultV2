"""Data transfer objects for use case inputs/outputs."""

from anivault.application.dto.match_result import (
    GroupMatchResultDTO,
    MatchFileRow,
    MatchInput,
    MatchResult,
)
from anivault.application.dto.progress import ProgressEvent
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO

__all__ = [
    "GroupMatchResultDTO",
    "MatchFileRow",
    "MatchInput",
    "MatchResult",
    "ProgressEvent",
    "TmdbSeriesCandidateDTO",
]
