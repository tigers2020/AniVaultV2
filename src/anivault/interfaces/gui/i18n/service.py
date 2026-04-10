"""Qt-backed i18n service: current language, translate, and broadcast signal."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal

from anivault.constants.gui.settings import DEFAULT_UI_LANGUAGE, normalize_ui_language
from anivault.interfaces.gui.i18n.catalog import CATALOG

_SERVICE: I18nService | None = None


class I18nService(QObject):
    """Holds current UI language and emits when it changes."""

    language_changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._language = DEFAULT_UI_LANGUAGE

    def get_current_language(self) -> str:
        return self._language

    def set_current_language(self, language: str, *, emit_signal: bool = True) -> str:
        normalized = normalize_ui_language(language)
        previous = self._language
        self._language = normalized
        if emit_signal and normalized != previous:
            self.language_changed.emit(normalized)
        return normalized


def get_i18n_service() -> I18nService:
    """Return the process-wide I18nService (lazy, requires QApplication for signals)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = I18nService()
    return _SERVICE


def translate(key: str, **params: Any) -> str:
    """Return message for key in current language, then ko, then the key itself."""
    lang = get_i18n_service().get_current_language()
    table = CATALOG.get(lang) or {}
    text = table.get(key)
    if text is None:
        text = CATALOG.get(DEFAULT_UI_LANGUAGE, {}).get(key)
    if text is None:
        return key
    if params:
        try:
            return str(text).format(**params)
        except (KeyError, ValueError, IndexError):
            return str(text)
    return str(text)


def init_i18n_from_settings(*, emit_signal: bool = False) -> None:
    """Load language from merged settings into the i18n service."""
    from anivault.interfaces.gui.settings_storage import load_all

    data = load_all()
    raw = data.get("language", DEFAULT_UI_LANGUAGE)
    get_i18n_service().set_current_language(str(raw), emit_signal=emit_signal)
