from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QScrollArea, QTabWidget, QWidget

from anivault.interfaces.gui import app as app_module
from anivault.interfaces.gui import i18n as i18n_module
from anivault.interfaces.gui import main as main_module
from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.i18n import get_i18n_service, translate
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.pages import organizer_page as organizer_page_module
from anivault.interfaces.gui.pages.organizer_page import OrganizerPage
from anivault.interfaces.gui.pages.settings_page import SettingsPage
from anivault.interfaces.gui.presenters import settings_presenter as settings_presenter_module
from anivault.interfaces.gui.presenters.settings_presenter import SettingsPresenter
from anivault.interfaces.gui.templates.main_shell import MainShell


def _ensure_app() -> QApplication:
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def test_main_window_helper_methods_delegate_to_shell_and_theme(monkeypatch) -> None:
    window = MainWindow.__new__(MainWindow)
    shell = MagicMock()
    window._shell = shell  # type: ignore[attr-defined]
    window._tab_to_index = {"organizer": 2}  # type: ignore[attr-defined]
    window._startup_progress_reset_done = False  # type: ignore[attr-defined]
    window._progress_dialog = MagicMock()  # type: ignore[attr-defined]
    timer = MagicMock()
    window._responsive_timer = timer  # type: ignore[attr-defined]
    window.size = lambda: SimpleNamespace(width=lambda: 1280, height=lambda: 720)  # type: ignore[attr-defined]
    monkeypatch.setattr(
        app_module,
        "translate",
        lambda key, **kw: {
            app_module.PAGE_ORGANIZER_TITLE: "Organize",
            app_module.PAGE_ORGANIZER_DESC: "Desc",
        }.get(key, key),
    )
    density_calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        app_module,
        "set_responsive_density_for_size",
        lambda width, height: density_calls.append((width, height)),
    )
    super_calls: list[object] = []
    monkeypatch.setattr(
        app_module.QMainWindow, "resizeEvent", lambda self, event: super_calls.append(event)
    )
    monkeypatch.setattr(
        app_module.QMainWindow, "showEvent", lambda self, event: super_calls.append(event)
    )

    window._on_tab_clicked("organizer")  # type: ignore[attr-defined]
    window.resizeEvent("event")  # type: ignore[arg-type]
    window._apply_responsive_density()  # type: ignore[attr-defined]
    window.showEvent("show")  # type: ignore[arg-type]
    window.showEvent("show-again")  # type: ignore[arg-type]

    shell.set_topbar_page.assert_called_once_with("Organize", "Desc")
    shell.set_current_page.assert_called_once_with(2)
    timer.start.assert_called_once_with(app_module.MAIN_WINDOW_RESIZE_DEBOUNCE_MS)
    assert density_calls == [(1280, 720)]
    assert super_calls == ["event", "show", "show-again"]
    window._progress_dialog.hide_progress.assert_called_once()  # type: ignore[attr-defined]


def test_main_shell_and_settings_page_constructors(monkeypatch) -> None:
    _ensure_app()

    shell = MainShell()
    emitted: list[str] = []
    shell.tab_clicked.connect(lambda tab_id: emitted.append(tab_id))
    shell._on_tab_clicked("settings")  # type: ignore[attr-defined]
    shell.set_topbar_page("Title", "Description")
    shell.add_page(QWidget())
    shell.set_current_page(0)

    assert emitted == ["settings"]
    assert shell.topbar() is shell._topbar  # type: ignore[attr-defined]
    assert shell.sidebar() is shell._sidebar  # type: ignore[attr-defined]

    class FakeScanBuildCard(QWidget):
        settings_changed = Signal()

    class FakeAppearanceCard(QWidget):
        theme_changed = Signal(str)
        language_changed = Signal(str)

    class FakePathRulesForm(QWidget):
        pass

    class FakeParseTmdbForm(QWidget):
        pass

    class FakeBar(QObject):
        save_clicked = Signal()
        reset_clicked = Signal()
        load_clicked = Signal()

    class FakeSettingsActionsCard(QWidget):
        def __init__(self):
            super().__init__()
            self._bar = FakeBar()

        def action_bar(self):
            return self._bar

    class FakePresenter(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.forms = None
            self.load_calls = 0

        def set_forms(self, *forms):
            self.forms = forms

        def on_theme_changed(self, *_args):
            pass  # test stub: signals not exercised in this case

        def on_language_changed(self, *_args):
            pass  # test stub: signals not exercised in this case

        def on_save_clicked(self):
            pass  # test stub: signals not exercised in this case

        def on_reset_clicked(self):
            pass  # test stub: signals not exercised in this case

        def on_load_clicked(self):
            self.load_calls += 1

    from anivault.interfaces.gui.pages import settings_page as settings_page_module

    monkeypatch.setattr(settings_page_module, "ScanBuildCard", FakeScanBuildCard)
    monkeypatch.setattr(settings_page_module, "AppearanceCard", FakeAppearanceCard)
    monkeypatch.setattr(settings_page_module, "PathRulesForm", FakePathRulesForm)
    monkeypatch.setattr(settings_page_module, "ParseTmdbForm", FakeParseTmdbForm)
    monkeypatch.setattr(settings_page_module, "SettingsActionsCard", FakeSettingsActionsCard)
    monkeypatch.setattr(settings_page_module, "SettingsPresenter", FakePresenter)
    monkeypatch.setattr(settings_page_module.theme, "scroll_area_transparent", lambda: "scroll")
    monkeypatch.setattr(settings_page_module.theme, "page_section_gap_px", lambda: 19)
    monkeypatch.setattr(settings_page_module.theme, "settings_page_section_gap_px", lambda: 21)
    monkeypatch.setattr(settings_page_module.theme, "settings_tab_content_margins_px", lambda: 11)

    page = SettingsPage()
    assert isinstance(page, QWidget)
    assert isinstance(page._presenter, FakePresenter)  # type: ignore[attr-defined]
    assert page._presenter.forms is not None  # type: ignore[attr-defined]
    page_layout = page.layout()
    assert page_layout is not None
    assert page_layout.spacing() == 21
    tabs_item = page_layout.itemAt(0)
    assert tabs_item is not None
    tabs = tabs_item.widget()
    assert isinstance(tabs, QTabWidget)
    assert tabs.count() == 3
    assert tabs.tabText(0) == translate(K.SETTINGS_TAB_GENERAL)
    assert tabs.tabText(1) == translate(K.SETTINGS_TAB_PATHS)
    assert tabs.tabText(2) == translate(K.SETTINGS_TAB_PARSE_TMDB)

    actions_item = page_layout.itemAt(1)
    assert actions_item is not None
    assert actions_item.widget() is not None
    assert actions_item.widget().objectName() == "settings_actions_card"

    general_scroll = tabs.widget(0)
    assert isinstance(general_scroll, QScrollArea)
    general_inner = general_scroll.widget()
    assert general_inner is not None
    general_layout = general_inner.layout()
    assert general_layout is not None
    assert general_layout.spacing() == 21
    assert general_layout.contentsMargins().left() == 11
    general_scan = general_layout.itemAt(0)
    general_appearance = general_layout.itemAt(1)
    assert general_scan is not None
    assert general_appearance is not None
    assert general_scan.widget() is not None
    assert general_appearance.widget() is not None
    assert general_scan.widget().objectName() == "settings_scan_card"
    assert general_appearance.widget().objectName() == "settings_appearance_card"

    paths_scroll = tabs.widget(1)
    assert isinstance(paths_scroll, QScrollArea)
    paths_inner = paths_scroll.widget()
    assert paths_inner is not None
    paths_layout = paths_inner.layout()
    assert paths_layout is not None
    paths_item = paths_layout.itemAt(0)
    assert paths_item is not None
    assert paths_item.widget() is not None
    assert paths_item.widget().objectName() == "settings_path_rules_card"

    parse_scroll = tabs.widget(2)
    assert isinstance(parse_scroll, QScrollArea)
    parse_inner = parse_scroll.widget()
    assert parse_inner is not None
    parse_layout = parse_inner.layout()
    assert parse_layout is not None
    parse_item = parse_layout.itemAt(0)
    assert parse_item is not None
    assert parse_item.widget() is not None
    assert parse_item.widget().objectName() == "settings_parse_tmdb_card"

    get_i18n_service().set_current_language("en", emit_signal=False)
    page.retranslate_ui()
    assert tabs.tabText(0) == "General"
    assert tabs.tabText(1) == "Folders"
    assert tabs.tabText(2) == "Filenames & TMDB"

    assert page._presenter.load_calls == 0  # type: ignore[attr-defined]

    presenter = FakePresenter()
    page_with_presenter = SettingsPage(presenter=cast(SettingsPresenter, presenter))
    assert page_with_presenter._presenter is cast(SettingsPresenter, presenter)


def test_main_window_constructor_wires_pages_and_timer(monkeypatch) -> None:
    _ensure_app()

    class FakeShell(QWidget):
        tab_clicked = Signal(str)

        def __init__(self):
            super().__init__()
            self.pages: list[QWidget] = []

        def add_page(self, page: QWidget) -> None:
            self.pages.append(page)

        def set_topbar_page(self, *_args) -> None:
            pass  # test stub: MainWindow only records add_page

        def set_current_page(self, *_args) -> None:
            pass  # test stub: MainWindow only records add_page

        def retranslate_ui(self) -> None:
            # i18n refresh not exercised in this constructor wiring test.
            pass

    class FakeProgressDialog(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)

        def retranslate_ui(self) -> None:
            # Progress dialog strings not retranslated in this stub.
            pass

    class FakePipelineTableModel(QObject):
        def __init__(self):
            super().__init__()

    monkeypatch.setattr(app_module, "MainShell", FakeShell)
    monkeypatch.setattr(app_module, "ProgressDialog", FakeProgressDialog)

    import sys
    import types

    fake_models: Any = types.ModuleType("anivault.interfaces.gui.models")
    fake_models.PipelineTableModel = FakePipelineTableModel
    monkeypatch.setitem(sys.modules, "anivault.interfaces.gui.models", fake_models)

    fake_container: Any = types.ModuleType("anivault.bootstrap.container")

    class FakeAppContainer:
        def create_organizer_page(self, **_kwargs):
            return QWidget()

        def create_subtitle_organizer_page(self, **_kwargs):
            return QWidget()

        def create_settings_page(self):
            return QWidget()

        def close(self) -> None:
            # Fake container: no resources to release in this test.
            pass

    fake_container.AniVaultAppContainer = FakeAppContainer
    monkeypatch.setitem(sys.modules, "anivault.bootstrap.container", fake_container)

    window = MainWindow()

    assert isinstance(window._shell, FakeShell)  # type: ignore[attr-defined]
    assert len(window._shell.pages) == 3  # type: ignore[attr-defined]
    assert set(window._tab_to_index) == {"organizer", "subtitles", "settings"}  # type: ignore[attr-defined]
    assert window.centralWidget() is window._shell  # type: ignore[attr-defined]
    window.close()


def test_clear_widget_stylesheets_and_theme_coordinator_methods(monkeypatch) -> None:
    child_a = MagicMock()
    child_b = MagicMock()
    root = MagicMock()
    root.findChildren.return_value = [child_a, child_b]
    main_module._clear_widget_stylesheets(root)
    root.setStyleSheet.assert_called_once_with("")
    child_a.setStyleSheet.assert_called_once_with("")
    child_b.setStyleSheet.assert_called_once_with("")

    coordinator = main_module._ThemeReapplyCoordinator.__new__(main_module._ThemeReapplyCoordinator)
    coordinator._app = SimpleNamespace(  # type: ignore[assignment]
        topLevelWidgets=lambda: [MagicMock(), MagicMock()],
        setStyleSheet=MagicMock(),
    )
    coordinator._window = SimpleNamespace(  # type: ignore[assignment]
        findChildren=lambda cls: [
            MagicMock(styleSheet=lambda: ""),
            MagicMock(styleSheet=lambda: "local"),
        ],
        styleSheet=lambda: "",
    )
    coordinator._batch_size = 1
    coordinator._pending_density = False
    coordinator._pending_color = False
    coordinator._clear_targets = []
    coordinator._clear_index = 0
    coordinator._timer = SimpleNamespace(isActive=lambda: False, start=MagicMock())  # type: ignore[assignment]
    monkeypatch.setattr(main_module, "global_stylesheet", lambda: "QSS")

    coordinator.request_color_change()  # type: ignore[attr-defined]
    coordinator.request_density_change()  # type: ignore[attr-defined]
    coordinator._start_color_batch()  # type: ignore[attr-defined]
    coordinator._continue_color_batch()  # type: ignore[attr-defined]
    coordinator._pending_color = True  # type: ignore[attr-defined]
    coordinator._process()  # type: ignore[attr-defined]

    assert coordinator._timer.start.call_count >= 2  # type: ignore[attr-defined]
    coordinator._app.setStyleSheet.assert_called()  # type: ignore[attr-defined]


def test_main_run_initializes_app_and_registers_theme_callbacks(monkeypatch) -> None:
    events: list[str] = []
    theme_callbacks: list[Callable[[], None]] = []
    density_callbacks: list[Callable[[], None]] = []

    class FakeApp:
        def __init__(self, argv):
            self.argv = argv
            self.stylesheet = None

        def setStyleSheet(self, value):  # NOSONAR S100 — mirrors QApplication API
            self.stylesheet = value
            events.append(f"style:{value}")

        def exec(self):  # NOSONAR S100 — mirrors QApplication API
            events.append("exec")
            return 0

        def topLevelWidgets(self):  # NOSONAR S100 — mirrors QApplication API
            return []

    class FakeWindow:
        def __init__(self):
            self.shown = False

        def show(self):
            self.shown = True
            events.append("show")

        def findChildren(self, _cls):  # NOSONAR S100 — mirrors QWidget API
            return []

        def styleSheet(self):  # NOSONAR S100 — mirrors QWidget API
            return ""

    class FakeCoordinator:
        def __init__(self, *, app, window):
            self.app = app
            self.window = window
            events.append("coordinator")

        def request_color_change(self):
            events.append("color")

        def request_density_change(self):
            events.append("density")

    monkeypatch.setattr(main_module, "load_into_os_environ", lambda: events.append("env"))
    monkeypatch.setattr(main_module, "load_saved_theme", lambda: events.append("theme"))
    monkeypatch.setattr(i18n_module, "init_i18n_from_settings", lambda **kwargs: None)
    monkeypatch.setattr(main_module, "QApplication", FakeApp)
    monkeypatch.setattr(main_module, "MainWindow", FakeWindow)
    monkeypatch.setattr(main_module, "_ThemeReapplyCoordinator", FakeCoordinator)
    monkeypatch.setattr(main_module, "global_stylesheet", lambda: "QSS")
    monkeypatch.setattr(
        main_module,
        "_clear_widget_stylesheets",
        lambda widget: events.append(f"clear:{type(widget).__name__}"),
    )
    monkeypatch.setattr(
        main_module, "on_theme_changed", lambda callback: theme_callbacks.append(callback)
    )
    monkeypatch.setattr(
        main_module, "on_density_changed", lambda callback: density_callbacks.append(callback)
    )
    monkeypatch.setattr(main_module.sys, "argv", ["anivault"])

    def _fake_sys_exit(code: int = 0) -> None:
        raise SystemExit(code)

    monkeypatch.setattr(main_module.sys, "exit", _fake_sys_exit)

    with pytest.raises(SystemExit) as exc_info:
        main_module.run()
    assert exc_info.value.code == 0

    assert events[:4] == ["env", "theme", "coordinator", "style:QSS"]
    assert events[-2:] == ["show", "exec"]
    assert len(theme_callbacks) == 1
    assert len(density_callbacks) == 1

    theme_callbacks[0]()
    density_callbacks[0]()
    assert "color" in events
    assert "density" in events


def test_settings_presenter_load_reset_save_and_theme(monkeypatch) -> None:
    presenter = SettingsPresenter.__new__(SettingsPresenter)
    presenter._path_rules_form = MagicMock()  # type: ignore[attr-defined]
    presenter._parse_tmdb_form = MagicMock()  # type: ignore[attr-defined]
    presenter._scan_build_card = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setattr(
        settings_presenter_module,
        "load_all",
        lambda: {
            "path_rules": {"target_root": "F:/Library"},
            "parse_tmdb": {"ignore_tokens": "x264"},
            "scan_build": {"source_path": "F:/Anime"},
        },
    )
    monkeypatch.setattr(settings_presenter_module, "read_tmdb_api_key", lambda: "api-key")
    monkeypatch.setattr(
        settings_presenter_module,
        "get_defaults",
        lambda: {
            "path_rules": {"target_root": ""},
            "parse_tmdb": {"ignore_tokens": ""},
            "scan_build": {"source_path": ""},
        },
    )
    saved: list[dict[str, object]] = []
    keys: list[str] = []
    themes: list[str] = []
    monkeypatch.setattr(settings_presenter_module, "save_all", lambda data: saved.append(data))
    monkeypatch.setattr(
        settings_presenter_module, "write_tmdb_api_key", lambda value: keys.append(value)
    )
    monkeypatch.setattr(
        settings_presenter_module, "set_current_theme", lambda name: themes.append(name)
    )
    monkeypatch.setattr(
        settings_presenter_module, "save_theme", lambda name: themes.append(f"saved:{name}")
    )
    presenter._path_rules_form.get_values.return_value = {"target_root": "F:/Library"}  # type: ignore[attr-defined]
    presenter._parse_tmdb_form.get_values.return_value = {
        "ignore_tokens": "x264",
        "season_folder_format": "Season{season:02}",
        "tmdb_api_key": "secret",
    }  # type: ignore[attr-defined]
    presenter._scan_build_card.get_values.return_value = {
        "source_path": "F:/Anime",
    }  # type: ignore[attr-defined]

    presenter._load_into_forms()  # type: ignore[attr-defined]
    presenter._on_settings_changed()  # type: ignore[attr-defined]
    presenter.on_reset_clicked()
    presenter.on_load_clicked()
    presenter.on_theme_changed("dark")

    presenter._path_rules_form.set_values.assert_called()  # type: ignore[attr-defined]
    assert saved and saved[-1]["scan_build"] == {"source_path": "F:/Anime"}
    assert keys == ["secret"]
    assert themes == ["dark", "saved:dark"]


def test_scan_build_card_emits_settings_changed_on_path_signal() -> None:
    _ensure_app()

    from anivault.interfaces.gui.components.organisms.scan_build_card import ScanBuildCard

    widget = ScanBuildCard()
    emitted: list[str] = []
    widget.settings_changed.connect(lambda: emitted.append("changed"))
    widget._source.path_changed.emit("F:/Anime")  # type: ignore[attr-defined]

    assert emitted == ["changed"]
    widget.close()


def test_folder_scan_bar_relays_selected_path() -> None:
    _ensure_app()

    from anivault.interfaces.gui.components.organisms.folder_scan_bar import FolderScanBar

    widget = FolderScanBar()
    emitted: list[str] = []
    widget.path_changed.connect(emitted.append)
    widget._path_field.path_changed.emit("F:/Anime")  # type: ignore[attr-defined]

    assert emitted == ["F:/Anime"]
    widget.close()


def test_organizer_page_helpers_update_stats_and_autoscan(monkeypatch) -> None:
    page = OrganizerPage.__new__(OrganizerPage)
    page._model = cast(
        Any,
        SimpleNamespace(
            flat_rows=lambda: [
                SimpleNamespace(parsed_title="Show", tmdb_korean_title_group="Show"),
                SimpleNamespace(parsed_title="", tmdb_korean_title_group=""),
            ],
            rowCount=lambda: 3,
        ),
    )
    page._stats_grid = MagicMock()  # type: ignore[attr-defined]
    page._scan_bar = MagicMock()  # type: ignore[attr-defined]
    page._presenter = cast(Any, SimpleNamespace(on_scan_clicked=MagicMock()))
    page._auto_scan_done = False  # type: ignore[attr-defined]
    save_calls: list[dict[str, object]] = []
    monkeypatch.setattr(organizer_page_module, "save_all", lambda data: save_calls.append(data))
    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Anime", "auto_scan_on_first_show": "yes"}},
    )
    super_calls: list[object] = []
    monkeypatch.setattr(
        organizer_page_module.QWidget, "showEvent", lambda self, event: super_calls.append(event)
    )
    single_shots: list[tuple[int, Callable[[], None]]] = []
    monkeypatch.setattr(
        organizer_page_module.QTimer,
        "singleShot",
        lambda delay, callback: single_shots.append((delay, callback)),
    )
    monkeypatch.setattr(organizer_page_module.Path, "is_dir", lambda self: True)

    page._on_scan_path_changed("F:/Anime")  # type: ignore[attr-defined]
    page._update_stats()  # type: ignore[attr-defined]
    page.showEvent("event")  # type: ignore[arg-type]

    assert save_calls == [{"scan_build": {"source_path": "F:/Anime"}}]
    page._stats_grid.set_stats.assert_called_once_with(scanned=2, parsed=1, tmdb_matches=1, groups=3)  # type: ignore[attr-defined]
    assert super_calls == ["event"]
    assert single_shots and single_shots[0][0] == 100
    single_shots[0][1]()
    page._presenter.on_scan_clicked.assert_called_once_with("F:/Anime")  # type: ignore[attr-defined]


def test_organizer_page_show_event_skips_autoscan_for_blank_or_missing_path(monkeypatch) -> None:
    page = OrganizerPage.__new__(OrganizerPage)
    page._scan_bar = MagicMock()  # type: ignore[attr-defined]
    page._presenter = cast(Any, SimpleNamespace(on_scan_clicked=MagicMock()))
    page._auto_scan_done = False  # type: ignore[attr-defined]

    super_calls: list[object] = []
    monkeypatch.setattr(
        organizer_page_module.QWidget, "showEvent", lambda self, event: super_calls.append(event)
    )
    single_shots: list[tuple[int, Callable[[], None]]] = []
    monkeypatch.setattr(
        organizer_page_module.QTimer,
        "singleShot",
        lambda delay, callback: single_shots.append((delay, callback)),
    )

    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "   ", "auto_scan_on_first_show": True}},
    )
    page.showEvent("blank")  # type: ignore[arg-type]

    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Missing", "auto_scan_on_first_show": True}},
    )
    monkeypatch.setattr(organizer_page_module.Path, "is_dir", lambda self: False)
    page.showEvent("missing")  # type: ignore[arg-type]

    assert super_calls == ["blank", "missing"]
    assert single_shots == []
    page._presenter.on_scan_clicked.assert_not_called()  # type: ignore[attr-defined]
    assert page._auto_scan_done is False  # type: ignore[attr-defined]


def test_organizer_page_show_event_does_not_persist_reloaded_path(monkeypatch) -> None:
    page = OrganizerPage.__new__(OrganizerPage)
    page._scan_bar = MagicMock()  # type: ignore[attr-defined]
    page._presenter = cast(Any, SimpleNamespace(on_scan_clicked=MagicMock()))
    page._auto_scan_done = True  # type: ignore[attr-defined]
    page._syncing_scan_path = False  # type: ignore[attr-defined]

    save_calls: list[dict[str, object]] = []
    monkeypatch.setattr(organizer_page_module, "save_all", lambda data: save_calls.append(data))
    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Anime", "auto_scan_on_first_show": True}},
    )
    monkeypatch.setattr(organizer_page_module.QWidget, "showEvent", lambda self, event: None)

    def _set_path(path: str) -> None:
        page._on_scan_path_changed(path)  # type: ignore[attr-defined]

    page._scan_bar.set_path.side_effect = _set_path  # type: ignore[attr-defined]

    page.showEvent("event")  # type: ignore[arg-type]

    assert save_calls == []
    page._scan_bar.set_path.assert_called_once_with("F:/Anime")  # type: ignore[attr-defined]


def test_organizer_page_constructor_wires_components(monkeypatch) -> None:
    _ensure_app()

    class FakeModel(QObject):
        modelReset = Signal()
        rowsInserted = Signal()
        rowsRemoved = Signal()
        dataChanged = Signal()

        def __init__(self):
            super().__init__()

        def flat_rows(self):
            return []

        def rowCount(self):
            return 0

    class FakePresenter(QObject):
        def __init__(self, pipeline_model=None, parent=None):
            super().__init__(parent)
            self.pipeline_model = pipeline_model
            self.dry_run_handler = None
            self.pipeline_busy_handler = None
            self.panel = None

        def on_scan_clicked(self, *_args):
            pass  # test stub: constructor wiring only

        def on_match_clicked(self):
            pass  # test stub: constructor wiring only

        def on_dry_run_clicked(self):
            pass  # test stub: constructor wiring only

        def on_manual_tmdb_match_clicked(self):
            pass  # test stub: constructor wiring only

        def set_dry_run_enabled_handler(self, handler):
            self.dry_run_handler = handler

        def set_pipeline_busy_handler(self, handler):
            self.pipeline_busy_handler = handler

        def refresh_pipeline_action_bar_state(self) -> None:
            # Organizer page stub: action bar state not asserted in this test.
            pass

        def set_pipeline_result_panel(self, panel):
            self.panel = panel

    class FakeScanBar(QWidget):
        scan_clicked = Signal(str)
        match_clicked = Signal()
        dry_run_clicked = Signal()
        path_changed = Signal(str)

        def __init__(self):
            super().__init__()
            self.path_value = ""
            self.dry_run_enabled = None

        def set_path(self, path: str) -> None:
            self.path_value = path

        def set_dry_run_enabled(self, enabled: bool) -> None:
            self.dry_run_enabled = enabled

        def set_pipeline_busy(self, busy: bool) -> None:
            self.pipeline_busy = busy

    class FakeStatsGrid(QWidget):
        def __init__(self):
            super().__init__()
            self.calls: list[dict[str, int]] = []

        def set_stats(self, **kwargs):
            self.calls.append(kwargs)

    class FakeResultPanel(QWidget):
        manual_match_requested = Signal()
        episode_overview_requested = Signal(int)

        def __init__(self, model=None):
            super().__init__()
            self.model = model

    monkeypatch.setattr(organizer_page_module, "PipelineTableModel", FakeModel)
    monkeypatch.setattr(organizer_page_module, "OrganizerPresenter", FakePresenter)
    monkeypatch.setattr(organizer_page_module, "FolderScanBar", FakeScanBar)
    monkeypatch.setattr(organizer_page_module, "StatsGrid", FakeStatsGrid)
    monkeypatch.setattr(organizer_page_module, "PipelineResultPanel", FakeResultPanel)
    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Anime"}},
    )

    page = OrganizerPage()

    assert isinstance(page._model, FakeModel)  # type: ignore[attr-defined]
    assert isinstance(page._presenter, FakePresenter)  # type: ignore[attr-defined]
    assert isinstance(page._scan_bar, FakeScanBar)  # type: ignore[attr-defined]
    assert isinstance(page._stats_grid, FakeStatsGrid)  # type: ignore[attr-defined]
    assert isinstance(page._result_panel, FakeResultPanel)  # type: ignore[attr-defined]
    assert page._scan_bar.path_value == "F:/Anime"  # type: ignore[attr-defined]
    assert page._scan_bar.objectName() == "organizer_command_bar"  # type: ignore[attr-defined]
    assert page._stats_grid.objectName() == "organizer_summary_grid"  # type: ignore[attr-defined]
    assert page._result_panel.objectName() == "organizer_results_panel"  # type: ignore[attr-defined]
    assert page._presenter.panel is page._result_panel  # type: ignore[attr-defined]
    assert page._presenter.dry_run_handler.__self__ is page._scan_bar  # type: ignore[attr-defined]
    assert page._presenter.dry_run_handler.__name__ == "set_dry_run_enabled"  # type: ignore[attr-defined]
    assert page._stats_grid.calls[-1] == {  # type: ignore[attr-defined]
        "scanned": 0,
        "parsed": 0,
        "tmdb_matches": 0,
        "groups": 0,
    }
    page.close()
