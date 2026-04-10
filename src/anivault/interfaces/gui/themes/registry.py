"""Theme registry and runtime state for GUI themes."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

from anivault.interfaces.gui.themes.responsive import DensityKey

ThemeFactory = Callable[..., object]
ThemeCallback = Callable[[], None]


@dataclass
class ThemeRegistry:
    """Mutable runtime registry for the current theme and density state."""

    themes: Mapping[str, ThemeFactory]
    default_theme_name: str
    config_dir: Path
    config_file: Path
    current_theme_name: str | None = None
    current_density_key: DensityKey = "standard"
    current_theme: object | None = None
    on_color_theme_changed: list[ThemeCallback] = field(default_factory=list)
    on_density_changed: list[ThemeCallback] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.current_theme_name is None:
            self.current_theme_name = self.default_theme_name

    def list_themes(self) -> list[str]:
        return list(self.themes.keys())

    def get_theme(self, name: str, *, scale: float, fallback: ThemeFactory) -> object:
        factory = self.themes.get(name, fallback)
        return factory(scale=scale)

    def ensure_current(self, *, scale: float) -> object:
        if self.current_theme is None:
            factory = self.themes[self.current_theme_name or self.default_theme_name]
            self.current_theme = factory(scale=scale)
        return self.current_theme

    def set_current_theme(self, name: str, *, scale: float, notify: bool = True) -> None:
        if name not in self.themes:
            return
        self.current_theme_name = name
        self.current_theme = self.themes[name](scale=scale)
        if notify:
            for callback in self.on_color_theme_changed:
                callback()

    def set_density_key(self, key: DensityKey, *, notify: bool = True) -> None:
        if key == self.current_density_key:
            return
        self.current_density_key = key
        self.current_theme = None
        if notify:
            for callback in self.on_density_changed:
                callback()

    def on_theme_changed(self, callback: ThemeCallback) -> None:
        self.on_color_theme_changed.append(callback)

    def on_density_key_changed(self, callback: ThemeCallback) -> None:
        self.on_density_changed.append(callback)

    def load_saved_theme(self, *, validate: Callable[[str], bool]) -> None:
        if not self.config_file.exists():
            return
        with suppress(OSError, ValueError, KeyError):
            data = json.loads(self.config_file.read_text(encoding="utf-8"))
            name = data.get("theme")
            if isinstance(name, str) and validate(name):
                self.current_theme_name = name
                self.current_theme = None

    def save_theme(self, name: str) -> None:
        """Write theme only; preserve nested objects (path_rules, etc.) for settings merge."""
        with suppress(OSError):
            self.config_dir.mkdir(parents=True, exist_ok=True)
            data: dict[str, object] = {}
            if self.config_file.exists():
                with suppress(OSError, ValueError):
                    loaded = json.loads(self.config_file.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        data = dict(loaded)
            data["theme"] = name
            self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
