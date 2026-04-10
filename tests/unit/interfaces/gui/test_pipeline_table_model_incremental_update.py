from __future__ import annotations

from unittest.mock import MagicMock

from PySide6.QtCore import QObject, Qt

from anivault.constants.gui.tables import PIPELINE_TABLE_COLUMNS
from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel, group_pipeline_rows


class _Spy(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def on_called(self, *_args: object) -> None:
        self.calls += 1


def _row(path: str, *, season: str = "", episode: str = "", group_title: str = "") -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="A",
        parse_group="A",
        tmdb_korean_title_group=group_title,
        tmdb_series_id="",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="",
        season=season,
        resolution="1080p",
        status="scanned",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode=episode,
    )


def test_update_rows_if_compatible_emits_data_changed_without_model_reset() -> None:
    model = PipelineTableModel()
    model.modelReset = MagicMock()  # type: ignore[method-assign]
    spy = _Spy()
    model.dataChanged.connect(spy.on_called)

    model.set_rows(group_pipeline_rows([_row("/a/1.mkv"), _row("/a/2.mkv")]))
    model.modelReset.reset_mock()
    spy.calls = 0

    ok = model.update_rows_if_compatible(
        group_pipeline_rows(
            [
                _row("/a/1.mkv", group_title="Korean"),
                _row("/a/2.mkv", group_title="Korean"),
            ]
        )
    )

    assert ok is True
    assert model.modelReset.call_count == 0
    assert spy.calls >= 1


def test_data_returns_blank_for_missing_season_instead_of_defaulting_to_one() -> None:
    model = PipelineTableModel()
    model.set_rows(group_pipeline_rows([_row("/a/1.mkv", season="", episode="67")]))

    season_column = next(
        index for index, (_label, key) in enumerate(PIPELINE_TABLE_COLUMNS) if key == "season"
    )
    episode_column = next(
        index for index, (_label, key) in enumerate(PIPELINE_TABLE_COLUMNS) if key == "episode"
    )

    assert model.data(model.index(0, season_column), Qt.ItemDataRole.DisplayRole) == ""
    assert model.data(model.index(0, episode_column), Qt.ItemDataRole.DisplayRole) == "67"


def test_grouped_rows_collapse_multiple_episode_values_into_range() -> None:
    grouped = group_pipeline_rows(
        [
            _row("/a/1.mkv", season="", episode="1"),
            _row("/a/2.mkv", season="", episode="2"),
            _row("/a/3.mkv", season="", episode="3"),
        ]
    )

    assert len(grouped) == 1
    assert grouped[0].episode == "1-3"


def test_grouped_rows_collapse_multiple_season_values_into_range() -> None:
    grouped = group_pipeline_rows(
        [
            _row("/a/1.mkv", season="1"),
            _row("/a/2.mkv", season="2"),
            _row("/a/3.mkv", season="3"),
        ]
    )

    assert len(grouped) == 1
    assert grouped[0].season == "1-3"


def test_grouped_rows_list_non_contiguous_seasons() -> None:
    grouped = group_pipeline_rows(
        [
            _row("/a/1.mkv", season="1"),
            _row("/a/2.mkv", season="3"),
            _row("/a/3.mkv", season="4"),
        ]
    )

    assert len(grouped) == 1
    assert grouped[0].season == "1,3,4"


def test_single_row_season_unchanged() -> None:
    grouped = group_pipeline_rows([_row("/a/1.mkv", season="2", episode="5")])
    assert len(grouped) == 1
    assert grouped[0].season == "2"
