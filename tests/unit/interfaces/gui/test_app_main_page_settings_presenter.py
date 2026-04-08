from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QWidget

from anivault.interfaces.gui import app as app_module
from anivault.interfaces.gui import main as main_module
from anivault.interfaces.gui.app import MainWindow
from anivault.interfaces.gui.pages.settings_page import SettingsPage
from anivault.interfaces.gui.pages import organizer_page as organizer_page_module
from anivault.interfaces.gui.pages.organizer_page import OrganizerPage
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
    timer = MagicMock()
    window._responsive_timer = timer  # type: ignore[attr-defined]
    window.size = lambda: SimpleNamespace(width=lambda: 1280, height=lambda: 720)  # type: ignore[attr-defined]
    monkeypatch.setattr(app_module, "PAGE_META", {"organizer": ("Organizer", "Desc")})
    density_calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        app_module,
        "set_responsive_density_for_size",
        lambda width, height: density_calls.append((width, height)),
    )
    super_calls: list[object] = []
    monkeypatch.setattr(app_module.QMainWindow, "resizeEvent", lambda self, event: super_calls.append(event))

    window._on_tab_clicked("organizer")  # type: ignore[attr-defined]
    window.resizeEvent("event")  # type: ignore[arg-type]
    window._apply_responsive_density()  # type: ignore[attr-defined]

    shell.set_topbar_page.assert_called_once_with("Organizer", "Desc")
    shell.set_current_page.assert_called_once_with(2)
    timer.start.assert_called_once_with(app_module.MAIN_WINDOW_RESIZE_DEBOUNCE_MS)
    assert density_calls == [(1280, 720)]
    assert super_calls == ["event"]


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
        scan_clicked = Signal(str)

    class FakeAppearanceCard(QWidget):
        theme_changed = Signal(str)

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

        def set_forms(self, *forms):
            self.forms = forms

        def on_scan_clicked(self, *_args):
            pass

        def on_theme_changed(self, *_args):
            pass

        def on_save_clicked(self):
            pass

        def on_reset_clicked(self):
            pass

        def on_load_clicked(self):
            pass

    from anivault.interfaces.gui.pages import settings_page as settings_page_module

    monkeypatch.setattr(settings_page_module, "ScanBuildCard", FakeScanBuildCard)
    monkeypatch.setattr(settings_page_module, "AppearanceCard", FakeAppearanceCard)
    monkeypatch.setattr(settings_page_module, "PathRulesForm", FakePathRulesForm)
    monkeypatch.setattr(settings_page_module, "ParseTmdbForm", FakeParseTmdbForm)
    monkeypatch.setattr(settings_page_module, "SettingsActionsCard", FakeSettingsActionsCard)
    monkeypatch.setattr(settings_page_module, "SettingsPresenter", FakePresenter)

    page = SettingsPage()
    assert isinstance(page, QWidget)
    assert isinstance(page._presenter, FakePresenter)  # type: ignore[attr-defined]
    assert page._presenter.forms is not None  # type: ignore[attr-defined]

    presenter = FakePresenter()
    page_with_presenter = SettingsPage(presenter=presenter)
    assert page_with_presenter._presenter is presenter  # type: ignore[attr-defined]


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
            pass

        def set_current_page(self, *_args) -> None:
            pass

    class FakeProgressDialog(QObject):
        def __init__(self, parent=None):
            super().__init__(parent)

    class FakePipelineTableModel(QObject):
        def __init__(self):
            super().__init__()

    monkeypatch.setattr(app_module, "MainShell", FakeShell)
    monkeypatch.setattr(app_module, "ProgressDialog", FakeProgressDialog)

    import sys
    import types

    fake_models = types.ModuleType("anivault.interfaces.gui.models")
    fake_models.PipelineTableModel = FakePipelineTableModel
    monkeypatch.setitem(sys.modules, "anivault.interfaces.gui.models", fake_models)

    fake_container = types.ModuleType("anivault.bootstrap.container")
    fake_container.create_organizer_page = lambda **_kwargs: QWidget()
    fake_container.create_subtitle_organizer_page = lambda **_kwargs: QWidget()
    fake_container.create_settings_page = lambda: QWidget()
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
    coordinator._app = SimpleNamespace(
        topLevelWidgets=lambda: [MagicMock(), MagicMock()],
        setStyleSheet=MagicMock(),
    )
    coordinator._window = SimpleNamespace(
        findChildren=lambda cls: [MagicMock(styleSheet=lambda: ""), MagicMock(styleSheet=lambda: "local")],
        styleSheet=lambda: "",
    )
    coordinator._batch_size = 1
    coordinator._pending_density = False
    coordinator._pending_color = False
    coordinator._clear_targets = []
    coordinator._clear_index = 0
    coordinator._timer = SimpleNamespace(isActive=lambda: False, start=MagicMock())
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
    theme_callbacks: list[object] = []
    density_callbacks: list[object] = []

    class FakeApp:
        def __init__(self, argv):
            self.argv = argv
            self.stylesheet = None

        def setStyleSheet(self, value):
            self.stylesheet = value
            events.append(f"style:{value}")

        def exec(self):
            events.append("exec")
            return 0

        def topLevelWidgets(self):
            return []

    class FakeWindow:
        def __init__(self):
            self.shown = False

        def show(self):
            self.shown = True
            events.append("show")

        def findChildren(self, _cls):
            return []

        def styleSheet(self):
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
    monkeypatch.setattr(main_module, "QApplication", FakeApp)
    monkeypatch.setattr(main_module, "MainWindow", FakeWindow)
    monkeypatch.setattr(main_module, "_ThemeReapplyCoordinator", FakeCoordinator)
    monkeypatch.setattr(main_module, "global_stylesheet", lambda: "QSS")
    monkeypatch.setattr(
        main_module, "_clear_widget_stylesheets", lambda widget: events.append(f"clear:{type(widget).__name__}")
    )
    monkeypatch.setattr(main_module, "on_theme_changed", lambda callback: theme_callbacks.append(callback))
    monkeypatch.setattr(main_module, "on_density_changed", lambda callback: density_callbacks.append(callback))
    monkeypatch.setattr(main_module.sys, "argv", ["anivault"])
    monkeypatch.setattr(main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)))

    try:
        main_module.run()
    except SystemExit as exc:
        assert exc.code == 0

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
    monkeypatch.setattr(settings_presenter_module, "write_tmdb_api_key", lambda value: keys.append(value))
    monkeypatch.setattr(settings_presenter_module, "set_current_theme", lambda name: themes.append(name))
    monkeypatch.setattr(settings_presenter_module, "save_theme", lambda name: themes.append(f"saved:{name}"))
    presenter._path_rules_form.get_values.return_value = {"target_root": "F:/Library"}  # type: ignore[attr-defined]
    presenter._parse_tmdb_form.get_values.return_value = {"ignore_tokens": "x264", "tmdb_api_key": "secret"}  # type: ignore[attr-defined]
    presenter._scan_build_card.get_values.return_value = {"source_path": "F:/Anime"}  # type: ignore[attr-defined]

    presenter._load_into_forms()  # type: ignore[attr-defined]
    presenter._on_settings_changed()  # type: ignore[attr-defined]
    presenter.on_reset_clicked()
    presenter.on_load_clicked()
    presenter.on_theme_changed("dark")
    presenter.on_scan_clicked("F:/Anime")
    presenter.on_parse_clicked()
    presenter.on_match_clicked()
    presenter.on_build_plan_clicked()

    presenter._path_rules_form.set_values.assert_called()  # type: ignore[attr-defined]
    assert saved and saved[-1]["scan_build"] == {"source_path": "F:/Anime"}
    assert keys == ["secret"]
    assert themes == ["dark", "saved:dark"]


def test_organizer_page_helpers_update_stats_and_autoscan(monkeypatch) -> None:
    page = OrganizerPage.__new__(OrganizerPage)
    page._model = SimpleNamespace(
        flat_rows=lambda: [
            SimpleNamespace(parsed_title="Show", tmdb_korean_title_group="Show"),
            SimpleNamespace(parsed_title="", tmdb_korean_title_group=""),
        ],
        rowCount=lambda: 3,
    )  # type: ignore[attr-defined]
    page._stats_grid = MagicMock()  # type: ignore[attr-defined]
    page._scan_bar = MagicMock()  # type: ignore[attr-defined]
    page._presenter = SimpleNamespace(on_scan_clicked=MagicMock())  # type: ignore[attr-defined]
    page._auto_scan_done = False  # type: ignore[attr-defined]
    save_calls: list[dict[str, object]] = []
    monkeypatch.setattr(organizer_page_module, "save_all", lambda data: save_calls.append(data))
    monkeypatch.setattr(
        organizer_page_module,
        "load_all",
        lambda: {"scan_build": {"source_path": "F:/Anime", "auto_scan_on_first_show": "yes"}},
    )
    super_calls: list[object] = []
    monkeypatch.setattr(organizer_page_module.QWidget, "showEvent", lambda self, event: super_calls.append(event))
    single_shots: list[tuple[int, object]] = []
    monkeypatch.setattr(
        organizer_page_module.QTimer,
        "singleShot",
        lambda delay, callback: single_shots.append((delay, callback)),
    )

    page._on_scan_path_changed("F:/Anime")  # type: ignore[attr-defined]
    page._update_stats()  # type: ignore[attr-defined]
    page.showEvent("event")  # type: ignore[arg-type]

    assert save_calls == [{"scan_build": {"source_path": "F:/Anime"}}]
    page._stats_grid.set_stats.assert_called_once_with(scanned=2, parsed=1, tmdb_matches=1, groups=3)  # type: ignore[attr-defined]
    assert super_calls == ["event"]
    assert single_shots and single_shots[0][0] == 100
    single_shots[0][1]()
    page._presenter.on_scan_clicked.assert_called_once_with("F:/Anime")  # type: ignore[attr-defined]


def test_organizer_page_constructor_wires_components(monkeypatch) -> None:
    _ensure_app()

    class FakeModel(QObject):
        modelReset = Signal()

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
            self.panel = None

        def on_scan_clicked(self, *_args):
            pass

        def on_match_clicked(self):
            pass

        def on_dry_run_clicked(self):
            pass

        def on_manual_tmdb_match_clicked(self):
            pass

        def set_dry_run_enabled_handler(self, handler):
            self.dry_run_handler = handler

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

    class FakeStatsGrid(QWidget):
        def __init__(self):
            super().__init__()
            self.calls: list[dict[str, int]] = []

        def set_stats(self, **kwargs):
            self.calls.append(kwargs)

    class FakeResultPanel(QWidget):
        manual_match_requested = Signal()

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
