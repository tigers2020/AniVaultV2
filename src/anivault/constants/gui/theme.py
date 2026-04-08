"""GUI theme, density, and layout constants."""

from __future__ import annotations

from typing import Final

FONT_FAMILY: Final[str] = "Segoe UI, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
FONT_TITLE: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 13pt; font-weight: 700;"
FONT_SUBTITLE: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 500;"
FONT_BODY: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 11pt; font-weight: 400;"
FONT_CAPTION: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 400;"
FONT_LARGE_TITLE: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 18pt; font-weight: 700;"
FONT_STAT: Final[str] = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 500;"

RADIUS_PX: Final[int] = 18
SIDEBAR_WIDTH_PX: Final[int] = 260
POSTER_MIN_CARD_WIDTH_BASE_PX: Final[int] = 150
POSTER_GRID_SPACING_BASE_PX: Final[int] = 13

MAIN_WINDOW_MIN_WIDTH: Final[int] = 1280
MAIN_WINDOW_MIN_HEIGHT: Final[int] = 768
MAIN_WINDOW_RESIZE_DEBOUNCE_MS: Final[int] = 300

TOPBAR_BOTTOM_MARGIN_PX: Final[int] = 22
TOPBAR_STACK_SPACING_PX: Final[int] = 6

SIDEBAR_MARGIN_LEFT_PX: Final[int] = 18
SIDEBAR_MARGIN_TOP_PX: Final[int] = 24
SIDEBAR_MARGIN_RIGHT_PX: Final[int] = 18
SIDEBAR_MARGIN_BOTTOM_PX: Final[int] = 24
SIDEBAR_NAV_SPACING_PX: Final[int] = 8

VIEW_TOGGLE_SPACING_PX: Final[int] = 8

POSTER_IMAGE_ASPECT_HW: Final[float] = 3 / 2
BACKDROP_IMAGE_ASPECT_HW: Final[float] = 2 / 5
COMPACT_BODY_HEIGHT_PX: Final[int] = 48
COMPACT_TITLE_ONLY_BODY_HEIGHT_PX: Final[int] = 28
NON_COMPACT_BODY_HEIGHT_PX: Final[int] = 100
CARD_LAYOUT_SPACING_COMPACT_PX: Final[int] = 6
CARD_LAYOUT_SPACING_POSTER_PX: Final[int] = 8

POSTER_GRID_MIN_CARD_WIDTH: Final[int] = 140
POSTER_GRID_SPACING: Final[int] = 12
POSTER_GRID_MARGINS: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)

DENSITY_KEY_COMPACT: Final[str] = "compact"
DENSITY_KEY_STANDARD: Final[str] = "standard"
DENSITY_KEY_EXPANDED: Final[str] = "expanded"
DENSITY_KEY_SPACIOUS: Final[str] = "spacious"

DENSITY_COMPACT_MAX_WIDTH: Final[int] = 1260
DENSITY_COMPACT_MAX_HEIGHT: Final[int] = 740
DENSITY_STANDARD_MAX_WIDTH: Final[int] = 1500
DENSITY_STANDARD_MAX_HEIGHT: Final[int] = 860
DENSITY_EXPANDED_MAX_WIDTH: Final[int] = 1780
DENSITY_EXPANDED_MAX_HEIGHT: Final[int] = 980
