"""GUI internationalization: catalogs, translate(), and language_changed."""

from __future__ import annotations

from anivault.interfaces.gui.i18n.keys import PIPELINE_HEADER_KEYS
from anivault.interfaces.gui.i18n.pipeline_status import translate_pipeline_status
from anivault.interfaces.gui.i18n.service import (
    I18nService,
    get_i18n_service,
    init_i18n_from_settings,
    translate,
)

__all__ = [
    "I18nService",
    "PIPELINE_HEADER_KEYS",
    "get_i18n_service",
    "init_i18n_from_settings",
    "translate",
    "translate_pipeline_status",
]
