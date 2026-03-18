"""Theme registry: get/set current theme, persistence, change callback."""

import json
from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from anivault.interfaces.gui.themes.dark import DarkTheme
from anivault.interfaces.gui.themes.light import LightTheme

_THEMES: dict[str, type] = {
    "dark": DarkTheme,
    "light": LightTheme,
}
_current_theme_name = "dark"
_current: DarkTheme | LightTheme | None = None
_on_theme_changed: list[Callable[[], None]] = []

CONFIG_DIR = Path.home() / ".anivault"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _ensure_current() -> DarkTheme | LightTheme:
    global _current
    if _current is None:
        _current = _THEMES[_current_theme_name]()
    return _current


def list_themes() -> list[str]:
    """Return available theme names."""
    return list(_THEMES.keys())


def get_theme(name: str) -> DarkTheme | LightTheme:
    """Get theme instance by name."""
    cls = _THEMES.get(name) or DarkTheme
    return cls()


def get_current_theme() -> DarkTheme | LightTheme:
    """Return current theme instance."""
    return _ensure_current()


def set_current_theme(name: str, notify: bool = True) -> None:
    """Set current theme and optionally notify listeners."""
    global _current, _current_theme_name
    if name not in _THEMES:
        return
    _current_theme_name = name
    _current = _THEMES[name]()
    if notify:
        for cb in _on_theme_changed:
            cb()


def get_current_theme_name() -> str:
    """Return current theme name."""
    return _current_theme_name


def on_theme_changed(callback: Callable[[], None]) -> None:
    """Register callback to run when theme changes."""
    _on_theme_changed.append(callback)


def load_saved_theme() -> None:
    """Load theme from config file. Call at app startup. Does not notify listeners."""
    if not CONFIG_FILE.exists():
        return
    with suppress(OSError, ValueError, KeyError):
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        name = data.get("theme")
        if name and name in _THEMES:
            set_current_theme(name, notify=False)


def save_theme(name: str) -> None:
    """Save theme to config file."""
    with suppress(OSError):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data: dict[str, str] = {}
        if CONFIG_FILE.exists():
            with suppress(OSError, ValueError):
                loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
        data["theme"] = name
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
