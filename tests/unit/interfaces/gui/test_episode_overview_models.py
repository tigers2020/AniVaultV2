from __future__ import annotations

from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.tmdb import TvSeasonEpisodeInfo, TvSeasonOverview
from anivault.interfaces.gui.models import (
    build_episode_slot_view_models,
    extract_episode_numbers,
    extract_first_season_number,
    group_pipeline_rows,
)


def _row(path: str, *, episode: str, season: str = "1") -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show",
        tmdb_series_id="1",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2024",
        season=season,
        episode=episode,
        resolution="1080p",
        status="matched",
        poster_url="",
        backdrop_url="",
        target_path="",
    )


def test_extract_episode_numbers_and_first_season_number() -> None:
    assert extract_episode_numbers("01-03") == [1, 2, 3]
    assert extract_episode_numbers("S01E07") == [1, 7]
    assert extract_first_season_number("S02") == 2
    assert extract_first_season_number("") == 1


def test_build_episode_slot_view_models_marks_missing_and_uses_first_sorted_file() -> None:
    group = group_pipeline_rows(
        [
            _row("F:/Anime/B Episode.mkv", episode="2"),
            _row("F:/Anime/A Episode.mkv", episode="2"),
            _row("F:/Anime/C Episode.mkv", episode="3"),
        ]
    )[0]
    overview = TvSeasonOverview(
        season_number=1,
        episodes=(
            TvSeasonEpisodeInfo(number=1, name="Start", still_url="https://img/1.jpg"),
            TvSeasonEpisodeInfo(number=2, name="Middle"),
            TvSeasonEpisodeInfo(number=3, name="End", still_url="https://img/3.jpg"),
        ),
    )

    slots = build_episode_slot_view_models(group, overview)

    assert [slot.number for slot in slots] == [1, 2, 3]
    assert slots[0].image_url == "https://img/1.jpg"
    assert slots[0].missing is True
    assert slots[1].image_url == ""
    assert slots[1].file_path == "F:/Anime/A Episode.mkv"
    assert slots[2].image_url == "https://img/3.jpg"
    assert slots[2].file_path == "F:/Anime/C Episode.mkv"
