"""Theme registry, persistence, and responsive density helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from anivault.constants.gui.settings import CONFIG_DIR, CONFIG_FILE, DEFAULT_THEME_NAME
from anivault.interfaces.gui.themes.dark import DarkTheme
from anivault.interfaces.gui.themes.light import LightTheme
from anivault.interfaces.gui.themes.registry import ThemeRegistry
from anivault.interfaces.gui.themes.responsive import DensityKey, choose_density_key, get_profile

_THEMES: dict[str, type] = {
    "dark": DarkTheme,
    "light": LightTheme,
}

_registry = ThemeRegistry(
    themes=_THEMES,
    default_theme_name=DEFAULT_THEME_NAME,
    config_dir=CONFIG_DIR,
    config_file=CONFIG_FILE,
)


def _ensure_current() -> DarkTheme | LightTheme:
    profile = get_profile(_registry.current_density_key)
    return cast(DarkTheme | LightTheme, _registry.ensure_current(scale=profile.scale))


def list_themes() -> list[str]:
    return _registry.list_themes()


def get_theme(name: str) -> DarkTheme | LightTheme:
    profile = get_profile(_registry.current_density_key)
    theme = _registry.get_theme(name, scale=profile.scale, fallback=DarkTheme)
    return cast(DarkTheme | LightTheme, theme)


def get_current_theme() -> DarkTheme | LightTheme:
    return _ensure_current()


def set_current_theme(name: str, notify: bool = True) -> None:
    profile = get_profile(_registry.current_density_key)
    _registry.set_current_theme(name, scale=profile.scale, notify=notify)


def get_current_density_key() -> DensityKey:
    return _registry.current_density_key


def set_responsive_density_key(key: DensityKey, notify: bool = True) -> None:
    _registry.set_density_key(key, notify=notify)


def set_responsive_density_for_size(*, width: int, height: int, notify: bool = True) -> DensityKey:
    key = choose_density_key(width=width, height=height)
    set_responsive_density_key(key, notify=notify)
    return key


def get_current_theme_name() -> str:
    return _registry.current_theme_name or DEFAULT_THEME_NAME


def on_theme_changed(callback: Callable[[], None]) -> None:
    _registry.on_theme_changed(callback)


def on_density_changed(callback: Callable[[], None]) -> None:
    _registry.on_density_key_changed(callback)


def load_saved_theme() -> None:
    _registry.config_dir = CONFIG_DIR
    _registry.config_file = CONFIG_FILE
    _registry.load_saved_theme(validate=lambda name: name in _THEMES)


def save_theme(name: str) -> None:
    _registry.config_dir = CONFIG_DIR
    _registry.config_file = CONFIG_FILE
    _registry.save_theme(name)
