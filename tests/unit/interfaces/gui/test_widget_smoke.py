from __future__ import annotations

from PySide6.QtCore import QEvent, QSize
from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QPushButton, QTableWidget

from anivault.constants.gui.components import (
    DETAILS_PANE_MANUAL_MATCH_BUTTON,
    DRY_RUN_DIALOG_BUTTON_APPLY,
    FOLDER_SCAN_BAR_BUTTON_DRY_RUN,
    FOLDER_SCAN_BAR_BUTTON_MATCH,
    FOLDER_SCAN_BAR_BUTTON_SCAN,
    SCAN_BUILD_CARD_BUTTON_SCAN,
)
from anivault.interfaces.gui.components.molecules.panel_header import PanelHeader
from anivault.interfaces.gui.components.molecules.poster_card import PosterCard
from anivault.interfaces.gui.components.molecules.settings_action_bar import SettingsActionBar
from anivault.interfaces.gui.components.molecules.stat_card import StatCard
from anivault.interfaces.gui.components.organisms.appearance_card import AppearanceCard
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import DetailsPane
from anivault.interfaces.gui.components.organisms.folder_scan_bar import FolderScanBar
from anivault.interfaces.gui.components.organisms.parse_tmdb_form import ParseTmdbForm
from anivault.interfaces.gui.components.organisms.path_rules_form import PathRulesForm
from anivault.interfaces.gui.components.organisms.poster_grid import PosterGrid
from anivault.interfaces.gui.components.organisms.scan_build_card import ScanBuildCard
from anivault.interfaces.gui.components.organisms.settings_actions_card import (
    SettingsActionsCard,
)
from anivault.interfaces.gui.components.organisms.stats_grid import StatsGrid
from anivault.interfaces.gui.dialogs.dry_run_dialog import DryRunDialog
from anivault.interfaces.gui.models import PipelineGroupRow, PipelineRow, group_pipeline_rows


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def _row(
    path: str,
    *,
    title: str = "Frieren",
    tmdb_title: str = "Frieren",
    season: str = "S01",
    episode: str = "E01",
    resolution: str = "1080p",
) -> PipelineRow:
    return PipelineRow(
        original_file=path,
        parsed_title=title,
        parse_group="frieren",
        tmdb_korean_title_group=tmdb_title,
        tmdb_series_id="1" if tmdb_title else "",
        tmdb_poster_path="/poster.jpg" if tmdb_title else "",
        tmdb_backdrop_path="/backdrop.jpg" if tmdb_title else "",
        year="2024",
        season=season,
        episode=episode,
        resolution=resolution,
        status="matched" if tmdb_title else "parsed",
        poster_url="https://example.com/poster.jpg" if tmdb_title else "",
        backdrop_url="https://example.com/backdrop.jpg" if tmdb_title else "",
        target_path=f"F:/Library/{title}.mkv" if tmdb_title else "",
    )


def _group(*rows: PipelineRow) -> PipelineGroupRow:
    return group_pipeline_rows(list(rows))[0]


def _button_by_text(widget, text: str) -> QPushButton:
    for button in widget.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"Button not found: {text}")


def _buttons(widget) -> list[QPushButton]:
    return widget.findChildren(QPushButton)


def test_panel_header_and_poster_card_public_behavior() -> None:
    _ensure_app()
    header = PanelHeader("Organizer", "A very long description that should be elided on resize.")
    header.resize(140, 48)
    header.show()

    poster = PosterCard(title="Poster", meta="Meta", path="F:/Library/Poster.mkv")
    compact = PosterCard(
        title="Compact",
        meta="Meta",
        image_url="https://example.com/image.jpg",
        variant="compact",
        image_aspect="backdrop",
        text_panel_overlay=True,
        title_only=True,
    )
    poster.resize(180, 320)
    compact.resize(180, 220)
    poster.show()
    compact.show()
    QApplication.processEvents()

    label_texts = [label.text() for label in header.findChildren(QLabel)]
    assert "Organizer" in label_texts
    assert any(text for text in label_texts if text != "Organizer")

    poster.set_title("Updated Poster")
    poster.set_path("F:/Library/Updated Poster.mkv")
    compact.set_pixmap(None)

    assert poster.image_url == ""
    assert compact.image_url == "https://example.com/image.jpg"
    assert poster.heightForWidth(180) >= poster.minimumHeight()
    assert compact.heightForWidth(180) >= compact.minimumHeight()
    assert isinstance(poster.sizeHint(), QSize)

    header.close()
    poster.close()
    compact.close()


def test_poster_grid_and_content_view_public_rows_flow() -> None:
    _ensure_app()
    single = _group(_row("F:/Anime/Frieren - 01.mkv"))
    multi = _group(
        _row("F:/Anime/Frieren - 01.mkv", episode="E01"),
        _row("F:/Anime/Frieren - 02.mkv", episode="E02"),
    )

    grid = PosterGrid(show_header=False)
    cards = [
        PosterCard(title=f"Show {index}", meta="2024 / S01", variant="compact")
        for index in range(3)
    ]
    grid.set_cards(cards)
    grid.resize(520, 600)
    grid.show()

    view = ContentView()
    selected: list[int] = []
    view.selection_changed.connect(selected.append)
    view.set_rows([single, multi])
    view.show()
    QApplication.processEvents()

    assert grid.cards() == cards
    assert grid.minimumHeight() >= 0
    assert len(view.poster_cards()) == 2
    assert selected == [0]

    meta_texts = [label.text() for label in view.findChildren(QLabel)]
    assert any("Frieren - 01.mkv" in text for text in meta_texts)

    grid.close()
    view.close()


def test_details_pane_parse_form_and_path_rules_public_round_trip() -> None:
    _ensure_app()
    pane = DetailsPane()
    group = _group(
        _row("F:/Anime/Frieren - 01.mkv"),
        _row("F:/Anime/Frieren - 02.mkv", episode="E02"),
    )
    clicks: list[str] = []
    pane.manual_match_requested.connect(lambda: clicks.append("manual"))
    pane.set_row(group)
    pane.show()

    _button_by_text(pane, DETAILS_PANE_MANUAL_MATCH_BUTTON).click()

    pane_texts = [label.text() for label in pane.findChildren(QLabel)]
    assert clicks == ["manual"]
    assert any("Frieren - 02.mkv" in text for text in pane_texts)

    form = ParseTmdbForm()
    form.set_values(
        {
            "tmdb_api_key": "updated",
            "ignore_tokens": "hevc",
            "video_extensions": ".mkv",
            "tmdb_search_mode": "Auto",
            "season_folder_format": "S{season}",
        }
    )
    values = form.get_values()
    assert values["tmdb_api_key"] == "updated"
    assert values["ignore_tokens"] == "hevc"

    path_rules = PathRulesForm()
    path_rules.set_values(
        {
            "target_root": "F:/Anime",
            "path_template": "{title}",
            "unknown_resolution": "Misc",
            "unknown_group_folder": "Etc",
        }
    )
    path_values = path_rules.get_values()
    assert path_values["target_root"] == "F:/Anime"
    assert path_values["unknown_group_folder"] == "Etc"

    pane.close()
    form.close()
    path_rules.close()


def test_scan_and_settings_widgets_public_signals(monkeypatch) -> None:
    _ensure_app()
    monkeypatch.setattr(
        "anivault.interfaces.gui.components.organisms.appearance_card.list_themes",
        lambda: ["dark", "light"],
    )
    monkeypatch.setattr(
        "anivault.interfaces.gui.components.organisms.appearance_card.get_current_theme_name",
        lambda: "dark",
    )

    appearance = AppearanceCard()
    themes: list[str] = []
    appearance.theme_changed.connect(themes.append)
    combo = appearance.findChildren(QComboBox)[0]
    combo.setCurrentIndex(1)
    QApplication.processEvents()
    assert themes[-1] == "light"

    folder = FolderScanBar()
    scans: list[str] = []
    matches: list[str] = []
    dry_runs: list[str] = []
    path_updates: list[str] = []
    folder.scan_clicked.connect(scans.append)
    folder.match_clicked.connect(lambda: matches.append("match"))
    folder.dry_run_clicked.connect(lambda: dry_runs.append("dry"))
    folder.path_changed.connect(path_updates.append)
    folder.set_path("F:/Anime")
    folder.set_dry_run_enabled(True)
    _button_by_text(folder, FOLDER_SCAN_BAR_BUTTON_SCAN).click()
    _button_by_text(folder, FOLDER_SCAN_BAR_BUTTON_MATCH).click()
    _button_by_text(folder, FOLDER_SCAN_BAR_BUTTON_DRY_RUN).click()
    folder.changeEvent(QEvent(QEvent.Type.FontChange))
    assert scans == ["F:/Anime"]
    assert matches == ["match"]
    assert dry_runs == ["dry"]
    assert path_updates

    scan_card = ScanBuildCard()
    scan_events: list[str] = []
    scan_card.scan_clicked.connect(scan_events.append)
    scan_card.set_values(
        {
            "source_path": "F:/NewAnime",
            "tmdb_mode": scan_card.get_values()["tmdb_mode"],
            "unknown_mode": scan_card.get_values()["unknown_mode"],
        }
    )
    _button_by_text(scan_card, SCAN_BUILD_CARD_BUTTON_SCAN).click()
    assert scan_card.get_values()["source_path"] == "F:/NewAnime"
    assert scan_events == ["F:/NewAnime"]

    stats = StatsGrid()
    stats.set_stats(scanned=1200, parsed=34, tmdb_matches=12, groups=7)
    stats.changeEvent(QEvent(QEvent.Type.StyleChange))
    stats_texts = [label.text() for label in stats.findChildren(QLabel)]
    assert "1,200" in stats_texts

    stat_card = StatCard("Label", "1")
    stat_card.set_value("99")
    assert "99" in [label.text() for label in stat_card.findChildren(QLabel)]

    actions = SettingsActionsCard()
    bar = actions.action_bar()
    saves: list[str] = []
    resets: list[str] = []
    loads: list[str] = []
    bar.save_clicked.connect(lambda: saves.append("save"))
    bar.reset_clicked.connect(lambda: resets.append("reset"))
    bar.load_clicked.connect(lambda: loads.append("load"))
    for button in bar.findChildren(QPushButton):
        button.click()
    assert saves == ["save"]
    assert resets == ["reset"]
    assert loads == ["load"]

    standalone_bar = SettingsActionBar()
    standalone_emitted: list[str] = []
    standalone_bar.save_clicked.connect(lambda: standalone_emitted.append("save"))
    _button_by_text(standalone_bar, "Save").click()
    assert standalone_emitted == ["save"]

    for widget in (appearance, folder, scan_card, stats, stat_card, actions, standalone_bar):
        widget.close()


def test_dry_run_dialog_public_table_and_apply_signal() -> None:
    _ensure_app()
    dialog = DryRunDialog(
        [
            ("F:/Anime/Frieren - 01.mkv", "F:/Library/Frieren/Frieren - 01.mkv"),
            ("F:/Anime/Frieren - 02.mkv", "F:/Library/Frieren/Frieren - 02.mkv"),
        ]
    )
    emitted: list[str] = []
    dialog.apply_requested.connect(lambda: emitted.append("apply"))

    table = dialog.findChildren(QTableWidget)[0]
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "F:/Anime/Frieren - 01.mkv"

    _button_by_text(dialog, DRY_RUN_DIALOG_BUTTON_APPLY).click()
    assert emitted == ["apply"]
    dialog.close()
