from __future__ import annotations

from pathlib import Path

from anivault.contracts.pipeline import PipelineRow
from anivault.interfaces.gui.models import PipelineGroupRow, group_pipeline_rows
from anivault.interfaces.gui.utils.pipeline_icon_context import (
    open_location_directory_for_group,
    tmdb_tv_series_https_url,
)


def _row(path: str, *, tmdb_id: str = "") -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="",
        tmdb_series_id=tmdb_id,
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season="",
        resolution="",
        status="parsed",
        poster_url="",
        backdrop_url="",
        target_path="",
    )


def test_tmdb_tv_series_https_url_accepts_digits_and_rejects_garbage() -> None:
    assert tmdb_tv_series_https_url(" 123 ") == "https://www.themoviedb.org/tv/123"
    assert tmdb_tv_series_https_url("") is None
    assert tmdb_tv_series_https_url("12a") is None


def test_open_location_directory_for_group_first_existing_file(tmp_path: Path) -> None:
    f1 = tmp_path / "a.mkv"
    f1.write_text("x", encoding="utf-8")
    f2 = tmp_path / "missing.mkv"
    group = group_pipeline_rows([_row(str(f1)), _row(str(f2))])[0]
    assert open_location_directory_for_group(group) == tmp_path.resolve()


def test_open_location_directory_for_group_skips_missing_until_found(tmp_path: Path) -> None:
    missing = tmp_path / "nope.mkv"
    f2 = tmp_path / "b.mkv"
    f2.write_text("y", encoding="utf-8")
    group = group_pipeline_rows([_row(str(missing)), _row(str(f2))])[0]
    assert open_location_directory_for_group(group) == tmp_path.resolve()


def test_open_location_directory_for_group_none_when_no_file_exists(tmp_path: Path) -> None:
    group = group_pipeline_rows([_row(str(tmp_path / "ghost.mkv"))])[0]
    assert open_location_directory_for_group(group) is None


def test_open_location_directory_single_member_group(tmp_path: Path) -> None:
    f = tmp_path / "one.mkv"
    f.write_text("z", encoding="utf-8")
    group = group_pipeline_rows([_row(str(f))])[0]
    assert isinstance(group, PipelineGroupRow)
    assert open_location_directory_for_group(group) == tmp_path.resolve()
