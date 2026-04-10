"""Map stored pipeline status strings to translated display text."""

from __future__ import annotations

from anivault.constants.gui.components import (
    PIPELINE_ROW_STATUS_MOVED,
    PIPELINE_ROW_STATUS_TMDB_CACHED,
    PIPELINE_ROW_STATUS_TMDB_MATCHED,
    SCAN_PARSE_COORDINATOR_STATUS_PARSED,
    SCAN_PARSE_COORDINATOR_STATUS_SCANNED,
)
from anivault.interfaces.gui.i18n import keys as K
from anivault.interfaces.gui.i18n.service import translate

# Canonical stored values (Korean) from coordinators / use cases → catalog keys.
_STATUS_TO_KEY: dict[str, str] = {
    SCAN_PARSE_COORDINATOR_STATUS_SCANNED: K.PIPELINE_STATUS_SCANNED,
    SCAN_PARSE_COORDINATOR_STATUS_PARSED: K.PIPELINE_STATUS_PARSED,
    PIPELINE_ROW_STATUS_TMDB_CACHED: K.PIPELINE_STATUS_TMDB_CACHED,
    PIPELINE_ROW_STATUS_MOVED: K.PIPELINE_STATUS_MOVED,
    PIPELINE_ROW_STATUS_TMDB_MATCHED: K.PIPELINE_STATUS_TMDB_MATCHED,
    "Mixed": K.PIPELINE_STATUS_MIXED,
    "혼합": K.PIPELINE_STATUS_MIXED,
}


def translate_pipeline_status(text: str) -> str:
    """Return localized label for a pipeline row/group status value."""
    raw = (text or "").strip()
    if not raw:
        return ""
    key = _STATUS_TO_KEY.get(raw)
    if key is not None:
        return translate(key)
    return raw


__all__ = ["translate_pipeline_status"]
