from __future__ import annotations

from unittest.mock import MagicMock

from anivault.interfaces.gui.models import PipelineRow, PipelineTableModel
from anivault.interfaces.gui.presenters import organizer_presenter
from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter


def _row() -> PipelineRow:
    return PipelineRow(
        original_file="F:/Anime/a.mkv",
        parsed_title="Show",
        parse_group="show",
        tmdb_korean_title_group="Show",
        tmdb_series_id="1",
        tmdb_poster_path="/poster.jpg",
        tmdb_backdrop_path="",
        year="2024",
        season="1",
        resolution="1080p",
        status="matched",
        poster_url="",
        backdrop_url="",
        target_path="",
    )


def test_presenter_constructs_all_coordinators(monkeypatch) -> None:
    created: list[tuple[str, object]] = []

    class FakeScanParseCoordinator:
        def __init__(self, presenter: OrganizerPresenter) -> None:
            created.append(("scan", presenter))

    class FakeMatchCoordinator:
        def __init__(self, presenter: OrganizerPresenter) -> None:
            created.append(("match", presenter))

    class FakePlanApplyCoordinator:
        def __init__(self, presenter: OrganizerPresenter) -> None:
            created.append(("plan", presenter))

    monkeypatch.setattr(organizer_presenter, "ScanParseCoordinator", FakeScanParseCoordinator)
    monkeypatch.setattr(organizer_presenter, "MatchCoordinator", FakeMatchCoordinator)
    monkeypatch.setattr(
        organizer_presenter,
        "PlanApplyCoordinator",
        FakePlanApplyCoordinator,
    )

    presenter = OrganizerPresenter(PipelineTableModel())

    assert created == [("scan", presenter), ("match", presenter), ("plan", presenter)]


def test_presenter_delegates_entrypoints_to_coordinators() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._scan_parse_coordinator = MagicMock()  # type: ignore[attr-defined]
    presenter._match_coordinator = MagicMock()  # type: ignore[attr-defined]
    presenter._plan_apply_coordinator = MagicMock()  # type: ignore[attr-defined]

    presenter.on_scan_clicked("F:/Anime")
    presenter.on_match_clicked()
    presenter.on_manual_tmdb_match_clicked()
    presenter.on_dry_run_clicked()

    presenter._scan_parse_coordinator.on_scan_clicked.assert_called_once_with("F:/Anime")  # type: ignore[attr-defined]
    presenter._match_coordinator.on_match_clicked.assert_called_once()  # type: ignore[attr-defined]
    presenter._match_coordinator.on_manual_tmdb_match_clicked.assert_called_once()  # type: ignore[attr-defined]
    presenter._plan_apply_coordinator.on_dry_run_clicked.assert_called_once()  # type: ignore[attr-defined]


def test_match_file_to_pipeline_row_uses_local_poster_when_available(monkeypatch) -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._title_match = MagicMock(  # type: ignore[attr-defined]
        get_poster_local_path=MagicMock(return_value="C:/poster.jpg")
    )
    monkeypatch.setattr(
        "anivault.interfaces.gui.presenters.organizer_presenter.resolve_final_poster_display_source",
        lambda local, remote: local or remote,
    )

    result = presenter._match_file_to_pipeline_row(_row())  # type: ignore[attr-defined]

    assert result.poster_url == "C:/poster.jpg"


def test_set_rows_groups_before_updating_model() -> None:
    presenter = OrganizerPresenter.__new__(OrganizerPresenter)
    presenter._model = MagicMock()  # type: ignore[attr-defined]

    presenter.set_rows([_row()])

    presenter._model.set_rows.assert_called_once()  # type: ignore[attr-defined]
