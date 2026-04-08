from __future__ import annotations

from PySide6.QtCore import QEvent, QSize
from PySide6.QtWidgets import QApplication, QPushButton

from anivault.interfaces.gui.components.organisms.appearance_card import AppearanceCard
from anivault.interfaces.gui.components.molecules.panel_header import PanelHeader
from anivault.interfaces.gui.components.molecules.poster_card import PosterCard
from anivault.interfaces.gui.components.molecules.settings_action_bar import SettingsActionBar
from anivault.interfaces.gui.components.molecules.stat_card import StatCard
from anivault.interfaces.gui.components.organisms.content_view import ContentView
from anivault.interfaces.gui.components.organisms.details_pane import (
    DetailsPane,
    _member_lines,
)
from anivault.interfaces.gui.components.organisms.folder_scan_bar import FolderScanBar
from anivault.interfaces.gui.components.organisms.parse_tmdb_form import ParseTmdbForm
from anivault.interfaces.gui.components.organisms.path_rules_form import (
    PathRulesForm,
    _path_template_label,
    _template_to_example,
)
from anivault.interfaces.gui.components.organisms.poster_grid import (
    PosterGrid,
    _GridContainer,
    _column_count,
)
from anivault.interfaces.gui.components.organisms.scan_build_card import ScanBuildCard
from anivault.interfaces.gui.components.organisms.settings_actions_card import (
    SettingsActionsCard,
)
from anivault.interfaces.gui.components.organisms.stats_grid import StatsGrid, _fmt
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


def test_panel_header_elides_description_on_resize() -> None:
    _ensure_app()
    header = PanelHeader("Organizer", "A very long description that should be elided on resize.")
    header.resize(140, 48)
    header.show()
    QApplication.processEvents()

    desc = header._desc_lbl  # type: ignore[attr-defined]
    assert desc is not None
    assert desc.text()

    header._apply_description_elide()  # type: ignore[attr-defined]
    assert len(desc.text()) <= len(header._description_text)  # type: ignore[attr-defined]
    header.close()


def test_poster_grid_container_and_cards_relayout() -> None:
    _ensure_app()
    assert _column_count(100, min_card=120, grid_spacing=12) == 1
    assert _column_count(500, min_card=120, grid_spacing=12) >= 3

    grid = PosterGrid(show_header=False)
    cards = [
        PosterCard(title=f"Show {index}", meta="2024 / S01", variant="compact")
        for index in range(3)
    ]
    grid.set_cards(cards)
    grid.resize(520, 600)
    grid.show()
    QApplication.processEvents()

    container = grid._container  # type: ignore[attr-defined]
    container.resize(520, 600)
    container._relayout()  # type: ignore[attr-defined]

    assert grid.cards() == cards
    assert container._last_cols >= 1  # type: ignore[attr-defined]
    assert container.minimumHeight() > 0

    empty = _GridContainer()
    empty._relayout()  # type: ignore[attr-defined]
    assert empty.minimumHeight() >= 0
    grid.close()
    empty.close()


def test_poster_card_resize_and_setters_cover_compact_and_poster_modes() -> None:
    _ensure_app()
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

    poster.set_title("Updated Poster")
    poster.set_path("F:/Library/Updated Poster.mkv")
    compact.set_pixmap(None)

    assert poster.image_url == ""
    assert compact.image_url == "https://example.com/image.jpg"
    assert poster.heightForWidth(180) >= poster.minimumHeight()
    assert compact.heightForWidth(180) >= compact.minimumHeight()
    assert isinstance(poster.sizeHint(), QSize)
    poster.close()
    compact.close()


def test_content_view_rows_and_selection_updates_metadata() -> None:
    _ensure_app()
    single = _group(_row("F:/Anime/Frieren - 01.mkv"))
    multi = _group(
        _row("F:/Anime/Frieren - 01.mkv", episode="E01"),
        _row("F:/Anime/Frieren - 02.mkv", episode="E02"),
    )
    view = ContentView()
    selected: list[int] = []
    view.selection_changed.connect(selected.append)

    assert "Frieren - 01.mkv" in _member_lines(multi)
    view.set_rows([single, multi])
    view._on_select(1)  # type: ignore[attr-defined]

    assert len(view.poster_cards()) == 2
    assert selected == [0, 1]
    assert "Frieren - 02.mkv" in view._meta_label.text()  # type: ignore[attr-defined]
    view._clear_list_widgets()  # type: ignore[attr-defined]
    assert view.poster_cards() == view._cards  # type: ignore[attr-defined]
    view.close()


def test_details_pane_handles_empty_single_and_group_rows() -> None:
    _ensure_app()
    pane = DetailsPane()
    single_row = _row("F:/Anime/Frieren - 01.mkv")
    group = _group(
        single_row,
        _row("F:/Anime/Frieren - 02.mkv", episode="E02"),
    )
    clicks: list[str] = []
    pane.manual_match_requested.connect(lambda: clicks.append("manual"))

    pane.set_row(None)
    assert not pane._manual_btn.isEnabled()  # type: ignore[attr-defined]

    pane.set_row(single_row)
    assert pane._manual_btn.isEnabled()  # type: ignore[attr-defined]
    assert "Frieren - 01.mkv" in pane._content.text()  # type: ignore[attr-defined]

    pane.set_row(group)
    pane._manual_btn.click()  # type: ignore[attr-defined]
    assert clicks == ["manual"]
    assert "Frieren - 02.mkv" in pane._content.text()  # type: ignore[attr-defined]
    pane.close()


def test_parse_tmdb_form_round_trip_and_signal_emission() -> None:
    _ensure_app()
    form = ParseTmdbForm()
    changes: list[str] = []
    form.settings_changed.connect(lambda: changes.append("changed"))

    form._tmdb_api_key.set_value("secret")  # type: ignore[attr-defined]
    form._ignore_tokens.set_value("x264")  # type: ignore[attr-defined]
    form._video_ext.set_value(".mkv,.mp4")  # type: ignore[attr-defined]
    form._season_format.set_value("Season {season}")  # type: ignore[attr-defined]
    form._tmdb_search.setCurrentIndex(0)  # type: ignore[attr-defined]

    values = form.get_values()
    assert values["tmdb_api_key"] == "secret"
    assert values["ignore_tokens"] == "x264"

    form.set_values(
        {
            "tmdb_api_key": "updated",
            "ignore_tokens": "hevc",
            "video_extensions": ".mkv",
            "tmdb_search_mode": values["tmdb_search_mode"],
            "season_folder_format": "S{season}",
        }
    )
    assert form.get_values()["tmdb_api_key"] == "updated"
    assert changes
    form.close()


def test_path_rules_form_helpers_and_round_trip() -> None:
    _ensure_app()
    assert _template_to_example("{title}/{season}") != "{title}/{season}"
    assert "Path template" in _path_template_label("{title}")

    form = PathRulesForm()
    changes: list[str] = []
    form.settings_changed.connect(lambda: changes.append("changed"))

    form._target_root.set_value("F:/Library")  # type: ignore[attr-defined]
    form._path_template.set_value("{title}/Season {season}")  # type: ignore[attr-defined]
    form._unknown_resolution.set_value("Unknown Resolution")  # type: ignore[attr-defined]
    form._unknown_group.set_value("Unknown Group")  # type: ignore[attr-defined]

    values = form.get_values()
    assert values["target_root"] == "F:/Library"
    assert values["path_template"] == "{title}/Season {season}"

    form.set_values(
        {
            "target_root": "F:/Anime",
            "path_template": "{title}",
            "unknown_resolution": "Misc",
            "unknown_group_folder": "Etc",
        }
    )
    assert form.get_values()["unknown_group_folder"] == "Etc"
    assert changes
    form.close()


def test_scan_build_card_get_set_and_scan_signal() -> None:
    _ensure_app()
    card = ScanBuildCard()
    scans: list[str] = []
    changes: list[str] = []
    card.scan_clicked.connect(scans.append)
    card.settings_changed.connect(lambda: changes.append("changed"))

    card._source.set_path("F:/Anime")  # type: ignore[attr-defined]
    card._on_scan()  # type: ignore[attr-defined]
    values = card.get_values()
    assert values["source_path"] == "F:/Anime"

    card.set_values(
        {
            "source_path": "F:/NewAnime",
            "tmdb_mode": values["tmdb_mode"],
            "unknown_mode": values["unknown_mode"],
        }
    )
    assert card.get_values()["source_path"] == "F:/NewAnime"
    assert scans == ["F:/Anime"]
    assert changes
    card.close()


def test_dry_run_dialog_populates_rows_and_emits_apply() -> None:
    _ensure_app()
    dialog = DryRunDialog(
        [
            ("F:/Anime/Frieren - 01.mkv", "F:/Library/Frieren/Frieren - 01.mkv"),
            ("F:/Anime/Frieren - 02.mkv", "F:/Library/Frieren/Frieren - 02.mkv"),
        ]
    )
    emitted: list[str] = []
    dialog.apply_requested.connect(lambda: emitted.append("apply"))

    assert dialog._table.rowCount() == 2  # type: ignore[attr-defined]
    assert dialog._table.item(0, 0).text() == "F:/Anime/Frieren - 01.mkv"  # type: ignore[attr-defined]

    dialog._on_apply_clicked()  # type: ignore[attr-defined]
    assert emitted == ["apply"]
    dialog.close()


def test_small_gui_cards_and_bars_cover_interactions(monkeypatch) -> None:
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
    appearance._theme_combo.setCurrentIndex(1)  # type: ignore[attr-defined]
    appearance._on_theme_selected()  # type: ignore[attr-defined]
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
    folder._on_scan()  # type: ignore[attr-defined]
    folder.match_clicked.emit()
    folder.dry_run_clicked.emit()
    folder.changeEvent(QEvent(QEvent.Type.FontChange))
    assert scans == ["F:/Anime"]
    assert matches == ["match"]
    assert dry_runs == ["dry"]
    assert path_updates

    assert _fmt(1200) == "1,200"
    stats = StatsGrid()
    stats.set_stats(scanned=1200, parsed=34, tmdb_matches=12, groups=7)
    stats.changeEvent(QEvent(QEvent.Type.StyleChange))
    assert stats._cards[0].layout().itemAt(1).widget().text() == "1,200"  # type: ignore[union-attr]

    stat_card = StatCard("Label", "1")
    stat_card.set_value("99")
    assert stat_card.layout().itemAt(1).widget().text() == "99"  # type: ignore[union-attr]

    actions = SettingsActionsCard()
    bar = actions.action_bar()
    saves: list[str] = []
    resets: list[str] = []
    loads: list[str] = []
    bar.save_clicked.connect(lambda: saves.append("save"))
    bar.reset_clicked.connect(lambda: resets.append("reset"))
    bar.load_clicked.connect(lambda: loads.append("load"))
    buttons = bar.findChildren(QPushButton)
    for widget in buttons:
        widget.click()
    assert saves == ["save"]
    assert resets == ["reset"]
    assert loads == ["load"]

    standalone_bar = SettingsActionBar()
    standalone_emitted: list[str] = []
    standalone_bar.save_clicked.connect(lambda: standalone_emitted.append("save"))
    for widget in standalone_bar.findChildren(QPushButton):
        widget.click()
        break
    assert standalone_emitted == ["save"]

    for widget in (appearance, folder, stats, stat_card, actions, standalone_bar):
        widget.close()
