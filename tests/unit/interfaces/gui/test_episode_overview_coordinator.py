from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.tmdb import TvSeasonEpisodeInfo, TvSeasonOverview
from anivault.interfaces.gui.models import PipelineGroupRow
from anivault.interfaces.gui.presenters.organizing import episode_overview_coordinator as module


class _Signal:
    def __init__(self) -> None:
        self.callbacks: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        self.callbacks.append(callback)

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in tuple(self.callbacks):
            callback(*args, **kwargs)


class _WorkerSignals:
    def __init__(self) -> None:
        self.result = _Signal()
        self.error = _Signal()


class _Worker:
    def __init__(self, *, execute_fn, input_dto, signals) -> None:
        self.execute_fn = execute_fn
        self.input_dto = input_dto
        self.signals = signals


def _row(path: str, *, tmdb_id: str = "1", season: str = "S01", episode: str = "1") -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show" if tmdb_id else "",
        tmdb_series_id=tmdb_id,
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


def test_open_group_index_warns_when_tmdb_match_missing(monkeypatch) -> None:
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        module.QMessageBox,
        "warning",
        lambda parent, title, message: warnings.append((title, message)),
    )
    presenter = SimpleNamespace(
        _tv_season_overview_execute=object(),
        _model=SimpleNamespace(rows=lambda: [PipelineGroupRow((_row("a.mkv", tmdb_id=""),))]),
        parent=lambda: None,
    )
    coord = module.EpisodeOverviewCoordinator(presenter)

    coord.open_group_index(0)

    assert warnings


def test_open_group_index_defaults_to_season_one_when_missing(monkeypatch) -> None:
    created_workers: list[_Worker] = []
    thread = object()
    dialog = MagicMock()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(
        module,
        "UseCaseWorker",
        lambda **kwargs: created_workers.append(_Worker(**kwargs)) or created_workers[-1],
    )
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(module.presenter_runtime, "register_worker_thread", MagicMock())
    monkeypatch.setattr(module, "EpisodeOverviewDialog", lambda parent=None: dialog)
    presenter = SimpleNamespace(
        _tv_season_overview_execute=object(),
        _model=SimpleNamespace(rows=lambda: [PipelineGroupRow((_row("a.mkv", season=""),))]),
        parent=lambda: None,
    )
    coord = module.EpisodeOverviewCoordinator(presenter)

    coord.open_group_index(0)

    assert created_workers[0].input_dto.season_number == 1


def test_open_group_index_starts_worker_and_populates_dialog(monkeypatch) -> None:
    created_workers: list[_Worker] = []
    thread = object()
    dialog = MagicMock()
    monkeypatch.setattr(module, "WorkerSignals", _WorkerSignals)
    monkeypatch.setattr(
        module,
        "UseCaseWorker",
        lambda **kwargs: created_workers.append(_Worker(**kwargs)) or created_workers[-1],
    )
    monkeypatch.setattr(module, "run_worker", lambda worker: thread)
    monkeypatch.setattr(module.presenter_runtime, "register_worker_thread", MagicMock())
    monkeypatch.setattr(module, "EpisodeOverviewDialog", lambda parent=None: dialog)

    presenter = SimpleNamespace(
        _tv_season_overview_execute=lambda *args: None,
        _model=SimpleNamespace(rows=lambda: [PipelineGroupRow((_row("a.mkv"),))]),
        parent=lambda: None,
    )
    coord = module.EpisodeOverviewCoordinator(presenter)

    coord.open_group_index(0)
    created_workers[0].signals.result.emit(
        TvSeasonOverview(
            season_number=2,
            episodes=(TvSeasonEpisodeInfo(number=1, name="Pilot"),),
        )
    )

    dialog.show_loading.assert_called_once()
    dialog.set_context.assert_any_call("Show", 2)
    dialog.show_slots.assert_called_once()


def test_on_error_warns_and_clears_dialog(monkeypatch) -> None:
    warnings: list[tuple[str, str]] = []
    monkeypatch.setattr(
        module.QMessageBox,
        "warning",
        lambda parent, title, message: warnings.append((title, message)),
    )
    presenter = SimpleNamespace(parent=lambda: None)
    coord = module.EpisodeOverviewCoordinator(presenter)
    dialog = MagicMock()

    coord._on_error(dialog, RuntimeError("boom"))

    dialog.show_empty.assert_called_once()
    assert warnings
