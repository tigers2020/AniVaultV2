"""Presentation row types for GUI. Qt Model consumes these only."""

from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class PipelineRow:
    """One row in pipeline table. Shared by table / poster / operations."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    target_path: str


def _aggregate_str(members: tuple[PipelineRow, ...], attr: str, *, mixed: str = "—") -> str:
    """Return common non-empty value or mixed marker."""
    vals = {(getattr(m, attr) or "").strip() for m in members}
    vals.discard("")
    if not vals:
        return ""
    if len(vals) == 1:
        return next(iter(vals))
    return mixed


@dataclass(frozen=True)
class PipelineGroupRow:
    """Several files with the same presentation group key (parsed title)."""

    members: tuple[PipelineRow, ...]

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError("PipelineGroupRow requires at least one member")

    @property
    def original_file(self) -> str:
        if len(self.members) == 1:
            return self.members[0].original_file
        return f"{len(self.members)}개 파일"

    @property
    def parsed_title(self) -> str:
        return _aggregate_str(self.members, "parsed_title")

    @property
    def parse_group(self) -> str:
        return _aggregate_str(self.members, "parse_group")

    @property
    def tmdb_korean_title_group(self) -> str:
        return _aggregate_str(self.members, "tmdb_korean_title_group")

    @property
    def year(self) -> str:
        return _aggregate_str(self.members, "year")

    @property
    def season(self) -> str:
        return _aggregate_str(self.members, "season")

    @property
    def resolution(self) -> str:
        return _aggregate_str(self.members, "resolution")

    @property
    def status(self) -> str:
        return _aggregate_str(self.members, "status")

    @property
    def poster_url(self) -> str:
        for m in self.members:
            if (m.poster_url or "").strip():
                return m.poster_url
        return ""

    @property
    def target_path(self) -> str:
        return _aggregate_str(self.members, "target_path")

    def representative(self) -> PipelineRow:
        """First member by path order; use for thumbnails and fallbacks."""
        return self.members[0]


def group_pipeline_rows(rows: list[PipelineRow]) -> list[PipelineGroupRow]:
    """Group rows by stripped parsed_title; empty title uses original_file as key."""
    buckets: OrderedDict[str, list[PipelineRow]] = OrderedDict()
    for r in rows:
        key = (r.parsed_title or "").strip()
        if not key:
            key = r.original_file
        buckets.setdefault(key, []).append(r)
    out: list[PipelineGroupRow] = []
    for members in buckets.values():
        sorted_members = tuple(sorted(members, key=lambda x: x.original_file))
        out.append(PipelineGroupRow(members=sorted_members))
    return out
