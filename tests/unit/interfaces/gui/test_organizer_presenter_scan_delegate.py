"""OrganizerPresenter scan entrypoint delegation tests."""

from anivault.interfaces.gui.models import PipelineTableModel
from anivault.interfaces.gui.presenters.organizer_presenter import OrganizerPresenter
from anivault.interfaces.gui.presenters.organizing import scan_parse_coordinator


def test_on_scan_clicked_delegates_to_scan_parse_coordinator(monkeypatch) -> None:
    calls: list[str] = []

    class FakeScanParseCoordinator:
        def __init__(self, presenter: OrganizerPresenter) -> None:
            self.presenter = presenter

        def on_scan_clicked(self, path: str) -> None:
            calls.append(path)

    monkeypatch.setattr(
        scan_parse_coordinator,
        "ScanParseCoordinator",
        FakeScanParseCoordinator,
    )
    presenter = OrganizerPresenter(PipelineTableModel())

    presenter.on_scan_clicked("F:/Anime")

    assert calls == ["F:/Anime"]
