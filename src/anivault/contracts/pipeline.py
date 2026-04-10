"""Pipeline and TMDB match contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PipelineRow:
    """Canonical row shared by application matching and GUI pipeline rendering."""

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
    episode: str = ""


@dataclass(frozen=True, slots=True)
class GroupMatchResult:
    """TMDB group match summary for a pipeline group."""

    group_key: str
    matched: bool
    tmdb_id: int | None
    korean_group_title: str
    original_title: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class MatchInput:
    """Input for the series match use case."""

    files: tuple[PipelineRow, ...] = field(default_factory=tuple)
    index_root_id: int | None = None


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Output from the series match use case."""

    files: tuple[PipelineRow, ...]
    groups: tuple[GroupMatchResult, ...] = field(default_factory=tuple)
