"""Match use case input/output."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class MatchFileRow:
    """One file row snapshot for matching (no GUI types)."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    tmdb_series_id: str
    tmdb_poster_path: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    target_path: str


@dataclass(slots=True)
class GroupMatchResultDTO:
    """Per-group match outcome for debugging / future UI."""

    group_key: str
    matched: bool
    tmdb_id: int | None
    korean_group_title: str
    original_title: str
    confidence: float
    reason: str


@dataclass(slots=True)
class MatchInput:
    """Input for match_series: one entry per file in pipeline order."""

    files: tuple[MatchFileRow, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class MatchResult:
    """Updated file rows after TMDB match; order preserved."""

    files: tuple[MatchFileRow, ...]
    groups: tuple[GroupMatchResultDTO, ...] = field(default_factory=tuple)
