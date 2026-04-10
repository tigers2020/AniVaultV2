"""GUI-facing pipeline row helpers."""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from anivault.contracts.pipeline import PipelineRow
from anivault.domain.rules.pipeline_grouping import pipeline_row_group_key


def pipeline_row_ready_for_plan(row: PipelineRow) -> bool:
    """Return True when a row has enough TMDB data for planning."""

    return bool((row.tmdb_korean_title_group or "").strip())


def pipeline_rows_ready_for_plan(rows: list[PipelineRow]) -> list[PipelineRow]:
    """Filter rows down to the ones that can be sent into planning."""

    return [row for row in rows if pipeline_row_ready_for_plan(row)]


def _aggregate_str(members: tuple[PipelineRow, ...], attr: str, *, mixed: str = "Mixed") -> str:
    values = {(getattr(member, attr) or "").strip() for member in members}
    values.discard("")
    if not values:
        return ""
    if len(values) == 1:
        return next(iter(values))
    return mixed


def _aggregate_resolution(members: tuple[PipelineRow, ...]) -> str:
    values = sorted({(member.resolution or "").strip() for member in members} - {""})
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return " / ".join(values)


def _episode_numbers_from_text(value: str) -> list[int]:
    text = (value or "").strip()
    if not text:
        return []
    range_match = re.fullmatch(r"(\d+)\s*[-~]\s*(\d+)", text)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if start <= end:
            return list(range(start, end + 1))
        return [start, end]
    if text.isdigit():
        return [int(text)]
    return [int(match) for match in re.findall(r"\d+", text)]


def _episode_numbers_to_text(values: list[int]) -> str:
    numbers: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        numbers.append(value)
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    if numbers == list(range(numbers[0], numbers[-1] + 1)):
        return f"{numbers[0]}-{numbers[-1]}"
    return ",".join(str(value) for value in numbers)


def _aggregate_episode(members: tuple[PipelineRow, ...]) -> str:
    numbers: list[int] = []
    for member in members:
        numbers.extend(_episode_numbers_from_text(member.episode))
    if numbers:
        return _episode_numbers_to_text(sorted(numbers))
    return _aggregate_str(members, "episode")


@dataclass(frozen=True)
class PipelineGroupRow:
    """Row group displayed in the GUI table."""

    members: tuple[PipelineRow, ...]
    _resolution_cached: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.members:
            raise ValueError("PipelineGroupRow requires at least one member")
        object.__setattr__(self, "_resolution_cached", _aggregate_resolution(self.members))

    @property
    def original_file(self) -> str:
        if len(self.members) == 1:
            return self.members[0].original_file
        return f"{len(self.members)} files"

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
    def episode(self) -> str:
        return _aggregate_episode(self.members)

    @property
    def resolution(self) -> str:
        return self._resolution_cached

    @property
    def status(self) -> str:
        return _aggregate_str(self.members, "status")

    @property
    def poster_url(self) -> str:
        for member in self.members:
            if (member.poster_url or "").strip():
                return member.poster_url
        return ""

    @property
    def backdrop_url(self) -> str:
        for member in self.members:
            if (member.backdrop_url or "").strip():
                return member.backdrop_url
        return ""

    @property
    def target_path(self) -> str:
        return _aggregate_str(self.members, "target_path")

    def representative(self) -> PipelineRow:
        return self.members[0]


def pipeline_group_display_image_url(group: PipelineGroupRow) -> str:
    """Prefer local poster sources over CDN sources for display."""

    def _local_or_file_first(url: str) -> bool:
        url_lower = url.lower()
        if url_lower.startswith("file:"):
            return True
        if url_lower.startswith(("http://", "https://")):
            return False
        try:
            return Path(url).is_file()
        except OSError:
            return False

    poster_url = (group.poster_url or "").strip()
    backdrop_url = (group.backdrop_url or "").strip()
    for url in (poster_url, backdrop_url):
        if url and _local_or_file_first(url):
            return url
    if backdrop_url:
        return backdrop_url
    return poster_url


def _pipeline_row_group_key(row: PipelineRow) -> str:
    return pipeline_row_group_key(row)


def group_pipeline_rows(rows: list[PipelineRow]) -> list[PipelineGroupRow]:
    """Group pipeline rows by TMDB id or parsed title while preserving input order."""

    buckets: OrderedDict[str, list[PipelineRow]] = OrderedDict()
    for row in rows:
        buckets.setdefault(_pipeline_row_group_key(row), []).append(row)
    grouped: list[PipelineGroupRow] = []
    for members in buckets.values():
        sorted_members = tuple(sorted(members, key=lambda item: item.original_file))
        grouped.append(PipelineGroupRow(members=sorted_members))
    return grouped
