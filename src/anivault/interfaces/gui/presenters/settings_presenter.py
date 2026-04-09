"""Settings page presenter."""

from typing import Any

from PySide6.QtCore import QObject

from anivault.bootstrap.env_file import read_tmdb_api_key, write_tmdb_api_key
from anivault.interfaces.gui.settings_storage import get_defaults, load_all, save_all
from anivault.interfaces.gui.themes import save_theme, set_current_theme


class SettingsPresenter(QObject):
    """Coordinate Settings form load/save/reset behavior."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._path_rules_form: Any = None
        self._parse_tmdb_form: Any = None
        self._scan_build_card: Any = None

    def set_forms(
        self,
        path_rules_form: Any,
        parse_tmdb_form: Any,
        scan_build_card: Any,
    ) -> None:
        self._path_rules_form = path_rules_form
        self._parse_tmdb_form = parse_tmdb_form
        self._scan_build_card = scan_build_card
        self._load_into_forms()
        if path_rules_form is not None:
            path_rules_form.settings_changed.connect(self._on_settings_changed)
        if parse_tmdb_form is not None:
            parse_tmdb_form.settings_changed.connect(self._on_settings_changed)
        if scan_build_card is not None:
            scan_build_card.settings_changed.connect(self._on_settings_changed)

    def _load_into_forms(self) -> None:
        data = load_all()
        if self._path_rules_form is not None and "path_rules" in data:
            self._path_rules_form.set_values(data["path_rules"])
        if self._parse_tmdb_form is not None and "parse_tmdb" in data:
            merged = dict(data["parse_tmdb"])
            merged["tmdb_api_key"] = read_tmdb_api_key()
            self._parse_tmdb_form.set_values(merged)
        if self._scan_build_card is not None and "scan_build" in data:
            self._scan_build_card.set_values(data["scan_build"])

    def _on_settings_changed(self) -> None:
        to_save: dict[str, Any] = {}
        if self._path_rules_form is not None:
            to_save["path_rules"] = self._path_rules_form.get_values()
        if self._parse_tmdb_form is not None:
            parse_vals = dict(self._parse_tmdb_form.get_values())
            api_key = parse_vals.pop("tmdb_api_key", "")
            to_save["parse_tmdb"] = parse_vals
            write_tmdb_api_key(api_key)
        if self._scan_build_card is not None:
            to_save["scan_build"] = self._scan_build_card.get_values()
        if to_save:
            save_all(to_save)

    def on_save_clicked(self) -> None:
        self._on_settings_changed()

    def on_reset_clicked(self) -> None:
        defaults = get_defaults()
        if self._path_rules_form is not None:
            self._path_rules_form.set_values(defaults["path_rules"])
        if self._parse_tmdb_form is not None:
            merged = dict(defaults["parse_tmdb"])
            merged["tmdb_api_key"] = read_tmdb_api_key()
            self._parse_tmdb_form.set_values(merged)
        if self._scan_build_card is not None:
            self._scan_build_card.set_values(defaults["scan_build"])

    def on_load_clicked(self) -> None:
        self._load_into_forms()

    def on_theme_changed(self, theme_name: str) -> None:
        set_current_theme(theme_name)
        save_theme(theme_name)
