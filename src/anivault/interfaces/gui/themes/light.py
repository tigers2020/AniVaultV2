"""Light theme palette overrides."""

from __future__ import annotations

from anivault.interfaces.gui.themes.base import ColorPalette
from anivault.interfaces.gui.themes.dark import DarkTheme

LIGHT_THEME_PALETTE = ColorPalette(
    bg="#f5f6fa",
    panel="#ffffff",
    panel2="#eef1f8",
    border="#c8d0e0",
    border_subtle="rgba(200, 208, 224, 0.5)",
    text="#1a2332",
    muted="#5c6b82",
    accent="#4a7aff",
    accent2="#2dd4a0",
    warn="#e09b2d",
    danger="#e0455c",
    ok="#22c55e",
    input_bg="rgba(255, 255, 255, 0.95)",
    table_bg="rgba(238, 241, 248, 0.9)",
    header_bg="rgba(232, 235, 242, 0.95)",
    sidebar_bg="rgba(248, 249, 252, 0.98)",
    card_bg="rgba(255, 255, 255, 0.95)",
)


class LightTheme(DarkTheme):
    """DarkTheme with a light palette and softer content overlay."""

    PALETTE = LIGHT_THEME_PALETTE
    CONTENT_VIEW_TEXT_PANEL_OVERLAY_BG = "rgba(0, 0, 0, 0.22)"
