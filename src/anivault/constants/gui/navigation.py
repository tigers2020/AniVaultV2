"""GUI navigation and page constants."""

from __future__ import annotations

from typing import Final

TAB_ORGANIZER: Final[str] = "organizer"
TAB_SUBTITLES: Final[str] = "subtitles"
TAB_SETTINGS: Final[str] = "settings"

VIEW_DETAILS: Final[str] = "details"
VIEW_CONTENT: Final[str] = "content"
VIEW_ICON_XL: Final[str] = "icon_xl"
VIEW_ICON_L: Final[str] = "icon_l"
VIEW_ICON_M: Final[str] = "icon_m"
VIEW_ICON_S: Final[str] = "icon_s"
VIEW_ICON_GROUP: Final[str] = "icon_group"

VIEW_TO_INDEX: Final[dict[str, int]] = {
    VIEW_DETAILS: 0,
    VIEW_CONTENT: 1,
    VIEW_ICON_XL: 2,
    VIEW_ICON_L: 3,
    VIEW_ICON_M: 4,
    VIEW_ICON_S: 5,
}

LEGACY_VIEW_KEY_MAP: Final[dict[str, str]] = {
    "tiles": VIEW_CONTENT,
    "list": VIEW_DETAILS,
}

ICON_SIZES: Final[dict[str, int]] = {
    VIEW_ICON_XL: 220,
    VIEW_ICON_L: 180,
    VIEW_ICON_M: 140,
    VIEW_ICON_S: 100,
}
