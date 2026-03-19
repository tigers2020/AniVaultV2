"""Theme base: ColorPalette and BaseTheme for QSS generation."""

from dataclasses import dataclass


@dataclass
class ColorPalette:
    """Color palette for a theme."""

    bg: str
    panel: str
    panel2: str
    border: str
    border_subtle: str
    text: str
    muted: str
    accent: str
    accent2: str
    warn: str
    danger: str
    ok: str
    input_bg: str
    table_bg: str
    header_bg: str
    sidebar_bg: str
    card_bg: str

    def to_dict(self) -> dict[str, str]:
        d = {
            "bg": self.bg,
            "panel": self.panel,
            "panel2": self.panel2,
            "border": self.border,
            "border_subtle": self.border_subtle,
            "text": self.text,
            "muted": self.muted,
            "accent": self.accent,
            "accent2": self.accent2,
            "warn": self.warn,
            "danger": self.danger,
            "ok": self.ok,
            "input_bg": self.input_bg,
            "table_bg": self.table_bg,
            "header_bg": self.header_bg,
            "sidebar_bg": self.sidebar_bg,
            "card_bg": self.card_bg,
        }
        return d


FONT_FAMILY = "Segoe UI, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
# Qt stylesheet does not reliably support CSS rem units.
# Prefer pt for font size to avoid pixel-size(pointSize=-1) warnings in Qt internals.
FONT_TITLE = f"font-family: {FONT_FAMILY}; font-size: 13pt; font-weight: 700;"
FONT_SUBTITLE = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 500;"
FONT_BODY = f"font-family: {FONT_FAMILY}; font-size: 11pt; font-weight: 400;"
FONT_CAPTION = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 400;"
FONT_LARGE_TITLE = f"font-family: {FONT_FAMILY}; font-size: 18pt; font-weight: 700;"
FONT_STAT = f"font-family: {FONT_FAMILY}; font-size: 10pt; font-weight: 500;"
RADIUS_PX = 18
SIDEBAR_WIDTH_PX = 260
