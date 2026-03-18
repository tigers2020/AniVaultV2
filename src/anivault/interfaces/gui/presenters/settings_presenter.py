"""SettingsPresenter: orchestrates SettingsPage. Path/parse/TMDB rules, scan/build, theme."""

from typing import Any

from PySide6.QtCore import QObject

from anivault.interfaces.gui.settings_storage import get_defaults, load_all, save_all
from anivault.interfaces.gui.themes import save_theme, set_current_theme


class SettingsPresenter(QObject):
    """Single orchestration for Settings page. Rules persistence, scan/build delegation."""

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
        """Inject form references. Call after page creates them."""
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
        """Load persisted settings into form widgets."""
        data = load_all()
        if self._path_rules_form is not None and "path_rules" in data:
            self._path_rules_form.set_values(data["path_rules"])
        if self._parse_tmdb_form is not None and "parse_tmdb" in data:
            self._parse_tmdb_form.set_values(data["parse_tmdb"])
        if self._scan_build_card is not None and "scan_build" in data:
            self._scan_build_card.set_values(data["scan_build"])

    def _on_settings_changed(self) -> None:
        """Persist settings when any form value changes."""
        to_save: dict[str, Any] = {}
        if self._path_rules_form is not None:
            to_save["path_rules"] = self._path_rules_form.get_values()
        if self._parse_tmdb_form is not None:
            to_save["parse_tmdb"] = self._parse_tmdb_form.get_values()
        if self._scan_build_card is not None:
            to_save["scan_build"] = self._scan_build_card.get_values()
        if to_save:
            save_all(to_save)

    def on_save_clicked(self) -> None:
        """Save current form values to config file."""
        self._on_settings_changed()

    def on_reset_clicked(self) -> None:
        """Reset forms to default values (does not save)."""
        defaults = get_defaults()
        if self._path_rules_form is not None:
            self._path_rules_form.set_values(defaults["path_rules"])
        if self._parse_tmdb_form is not None:
            self._parse_tmdb_form.set_values(defaults["parse_tmdb"])
        if self._scan_build_card is not None:
            self._scan_build_card.set_values(defaults["scan_build"])

    def on_load_clicked(self) -> None:
        """Reload settings from config file into forms."""
        self._load_into_forms()

    def on_theme_changed(self, theme_name: str) -> None:
        """Handle theme selection. Set theme and persist."""
        set_current_theme(theme_name)
        save_theme(theme_name)

    def on_scan_clicked(self, path: str) -> None:
        """Handle scan from ScanBuildCard. Delegates to Organizer flow."""
        pass

    def on_parse_clicked(self) -> None:
        """Handle parse button."""
        pass

    def on_match_clicked(self) -> None:
        """Handle TMDB query button."""
        pass

    def on_build_plan_clicked(self) -> None:
        """Handle build move plan button."""
        pass
