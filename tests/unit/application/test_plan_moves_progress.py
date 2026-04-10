"""Tests for plan_moves progress throttling and directory listing cache."""

from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest

from anivault.application.use_cases.plan_moves import make_execute
from anivault.constants.application.progress import PROGRESS_PERCENT_MAX
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.planning import PlanInput
from anivault.contracts.progress import ProgressEvent


def _row_for_index(index: int) -> PipelineRow:
    return PipelineRow(
        original_file=f"F:/Library/Series/Episode {index:05d}.mkv",
        parsed_title="Series",
        parse_group="Series",
        tmdb_korean_title_group="Series KO",
        tmdb_series_id="1",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="FHD",
        status="TMDB matched",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode=str(index % 12 + 1),
    )


def test_plan_moves_throttles_progress_callbacks() -> None:
    total_files = 800
    rows = tuple(_row_for_index(i) for i in range(total_files))
    events: list[ProgressEvent] = []

    def progress_cb(event: ProgressEvent) -> None:
        events.append(event)

    result = make_execute()(
        PlanInput(
            files=rows,
            path_template="{korean_title_group}/Season {season}/{original_file}",
            target_root="F:/AniVault/Organized",
            unknown_resolution="Unknown Resolution",
            unknown_group_folder="Unknown Title",
            include_companion_subtitles=False,
        ),
        progress_cb,
        Event(),
    )

    assert result.error is None
    assert events[0].current == 1
    assert events[-1].current == total_files
    assert events[-1].percent == PROGRESS_PERCENT_MAX
    assert len(events) <= PROGRESS_PERCENT_MAX + 2


def _matched_row(path: Path) -> PipelineRow:
    return PipelineRow(
        original_file=str(path),
        parsed_title="Parsed",
        parse_group="Parsed",
        tmdb_korean_title_group="Korean Title",
        tmdb_series_id="123",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2025",
        season="1",
        resolution="1080p",
        status="TMDB matched",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode="01",
    )


def test_plan_moves_reuses_parent_dir_listing_for_companions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    first = source_dir / "show-a.mkv"
    second = source_dir / "show-b.mkv"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    target_root = tmp_path / "organized"

    calls = 0
    orig_iterdir = Path.iterdir

    def wrapped_iterdir(self: Path):
        nonlocal calls
        result = orig_iterdir(self)
        try:
            if self.resolve() == source_dir.resolve():
                calls += 1
        except OSError:
            pass
        return result

    monkeypatch.setattr(Path, "iterdir", wrapped_iterdir)

    execute = make_execute()
    result = execute(
        PlanInput(
            files=(_matched_row(first), _matched_row(second)),
            path_template="{korean_title_group}/Season {season:02}/{original_filename}",
            target_root=str(target_root),
            unknown_resolution="Unknown",
            unknown_group_folder="Needs_Review",
            include_companion_subtitles=True,
        ),
        None,
        Event(),
    )

    assert result.error is None
    assert calls == 1
