from pathlib import Path
from threading import Event

from anivault.application.use_cases.plan_moves import make_execute
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.planning import PlanInput
from anivault.domain.models.path_template_input import PathTemplateInput
from anivault.domain.services.path_template import (
    effective_resolution_segment,
    render_destination_path,
)


def _path_template_input(
    original_file: str = "F:/Library/Series/Episode 01.mkv",
) -> PathTemplateInput:
    return PathTemplateInput(
        original_file=original_file,
        resolution="FHD",
        year="2024",
        season="1",
        korean_title_group="Series KO",
    )


def test_original_file_alias_matches_original_filename(tmp_path: Path) -> None:
    row = _path_template_input("F:/Library/Series/Episode 01.mkv")

    alias_dest = render_destination_path(
        "{korean_title_group}/Season {season}/{original_file}",
        row,
        target_root=str(tmp_path / "organized"),
        unknown_resolution="Unknown Resolution",
        unknown_group_folder="Unknown Title",
    )
    filename_dest = render_destination_path(
        "{korean_title_group}/Season {season}/{original_filename}",
        row,
        target_root=str(tmp_path / "organized"),
        unknown_resolution="Unknown Resolution",
        unknown_group_folder="Unknown Title",
    )

    assert alias_dest == filename_dest
    assert alias_dest.endswith(str(Path("Series KO") / "Season 1" / "Episode 01.mkv"))


def test_render_destination_path_does_not_require_existing_target(tmp_path: Path) -> None:
    missing_target = tmp_path / "missing" / "organized"

    dest = render_destination_path(
        "{korean_title_group}/Season {season}/{original_file}",
        _path_template_input(),
        target_root=str(missing_target),
        unknown_resolution="Unknown Resolution",
        unknown_group_folder="Unknown Title",
    )

    assert dest == str(missing_target / "Series KO" / "Season 1" / "Episode 01.mkv")
    assert not missing_target.exists()


def test_effective_resolution_segment_matches_render_fallback() -> None:
    row = PathTemplateInput(
        original_file="F:/Library/Series/Episode 01.mkv",
        resolution="",
        year="2024",
        season="1",
        korean_title_group="Series KO",
    )

    dest = render_destination_path(
        "{resolution}/{original_file}",
        row,
        target_root="F:/Organized",
        unknown_resolution="Unknown Resolution",
        unknown_group_folder="Unknown Title",
    )

    assert effective_resolution_segment("", "Unknown Resolution") == "Unknown Resolution"
    assert dest.endswith(str(Path("Unknown Resolution") / "Episode 01.mkv"))


def test_plan_moves_accepts_original_file_alias_for_large_batch() -> None:
    rows = tuple(
        PipelineRow(
            original_file=f"F:/Library/Series/Episode {index:05d}.mkv",
            parsed_title=f"Series {index // 12:04d}",
            parse_group=f"Series {index // 12:04d}",
            tmdb_korean_title_group=f"Series {index // 12:04d} KO",
            tmdb_series_id=str(index // 12 + 1),
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
        for index in range(10_000)
    )

    result = make_execute()(
        PlanInput(
            files=rows,
            path_template="{korean_title_group}/Season {season}/{original_file}",
            target_root="F:/AniVault/Organized",
            unknown_resolution="Unknown Resolution",
            unknown_group_folder="Unknown Title",
            include_companion_subtitles=False,
        ),
        None,
        Event(),
    )

    assert result.error is None
    assert len(result.moves) == len(rows)
    assert result.moves[0].destination_path.endswith(
        str(Path("Series 0000 KO") / "Season 1" / "Episode 00000.mkv")
    )
