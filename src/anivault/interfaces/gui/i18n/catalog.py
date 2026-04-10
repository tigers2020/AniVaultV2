"""Per-language string catalogs for GUI i18n."""

from __future__ import annotations

from .locales.en import MESSAGES as _EN_MESSAGES
from .locales.ko import MESSAGES as _KO_MESSAGES

CATALOG: dict[str, dict[str, str]] = {
    "ko": _KO_MESSAGES,
    "en": _EN_MESSAGES,
}
