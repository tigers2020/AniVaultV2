"""Theme facade: delegates to themes package.

Besides QSS string generation, this module also provides a few responsive
layout metric helpers that depend on the current density profile.
"""

from anivault.interfaces.gui.themes import get_current_density_key, get_current_theme
from anivault.interfaces.gui.themes.base import (
    FONT_BODY,
    FONT_CAPTION,
    FONT_FAMILY,
    FONT_LARGE_TITLE,
    FONT_STAT,
    FONT_SUBTITLE,
    FONT_TITLE,
    RADIUS_PX,
    SIDEBAR_WIDTH_PX,
)  # noqa: F401 — re-exported for consumers
from anivault.interfaces.gui.themes.responsive import DensityProfile, get_profile, scaled_int

__all__ = [
    "FONT_BODY",
    "FONT_CAPTION",
    "FONT_FAMILY",
    "FONT_LARGE_TITLE",
    "FONT_STAT",
    "FONT_SUBTITLE",
    "FONT_TITLE",
    "RADIUS_PX",
    "SIDEBAR_WIDTH_PX",
    "global_stylesheet",
    "main_bg",
    "scroll_area_transparent",
    "sidebar",
    "sidebar_nav_title",
    "sidebar_card",
    "sidebar_card_title",
    "sidebar_footer",
    "sidebar_footer_value",
    "topbar_title",
    "topbar_desc",
    "label_muted",
    "label_stat",
    "label_title",
    "line_edit",
    "combo_box",
    "pill",
    "step_index_label",
    "badge_label",
    "nav_item",
    "step_row_title",
    "step_row_text",
    "brand_title",
    "brand_subtitle",
    "stat_card",
    "stat_card_value",
    "panel_header_title",
    "panel_header_desc",
    "path_box",
    "poster_card",
    "poster_card_image",
    "poster_card_title",
    "poster_card_meta",
    "card_panel",
    "list_item",
    "list_item_strong",
    "list_item_muted",
    "form_label_muted",
    "view_toggle_button",
    "view_toggle_menu",
    "progress_dialog",
    # responsive metrics
    "sidebar_width_px",
    "tile_min_width_px",
    "tile_grid_spacing_px",
    "poster_min_card_width_px",
    "poster_grid_spacing_px",
]


def _t():
    return get_current_theme()


def __getattr__(name: str):
    if name == "COLORS":
        return _t().colors
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def global_stylesheet() -> str:
    return str(_t().global_stylesheet())


def main_bg() -> str:
    return _t().main_bg()


def scroll_area_transparent() -> str:
    return _t().scroll_area_transparent()


def sidebar() -> str:
    return _t().sidebar()


def sidebar_nav_title() -> str:
    return _t().sidebar_nav_title()


def sidebar_card() -> str:
    return _t().sidebar_card()


def sidebar_card_title() -> str:
    return _t().sidebar_card_title()


def sidebar_footer() -> str:
    return _t().sidebar_footer()


def sidebar_footer_value() -> str:
    return _t().sidebar_footer_value()


def topbar_title() -> str:
    return _t().topbar_title()


def topbar_desc() -> str:
    return _t().topbar_desc()


def label_muted() -> str:
    return _t().label_muted()


def label_stat() -> str:
    return _t().label_stat()


def label_title() -> str:
    return _t().label_title()


def line_edit() -> str:
    return _t().line_edit()


def combo_box() -> str:
    return _t().combo_box()


def pill(color: str = "blue") -> str:
    return _t().pill(color)


def step_index_label() -> str:
    return _t().step_index_label()


def badge_label(size: int) -> str:
    return _t().badge_label(size)


def nav_item() -> str:
    return _t().nav_item()


def step_row_title() -> str:
    return _t().step_row_title()


def step_row_text() -> str:
    return _t().step_row_text()


def brand_title() -> str:
    return _t().brand_title()


def brand_subtitle() -> str:
    return _t().brand_subtitle()


def stat_card() -> str:
    return _t().stat_card()


def stat_card_value() -> str:
    return _t().stat_card_value()


def panel_header_title() -> str:
    return _t().panel_header_title()


def panel_header_desc() -> str:
    return _t().panel_header_desc()


def path_box() -> str:
    return _t().path_box()


def poster_card() -> str:
    return _t().poster_card()


def poster_card_image() -> str:
    return _t().poster_card_image()


def poster_card_title() -> str:
    return _t().poster_card_title()


def poster_card_meta() -> str:
    return _t().poster_card_meta()


def card_panel() -> str:
    return _t().card_panel()


def list_item() -> str:
    return _t().list_item()


def list_item_strong() -> str:
    return _t().list_item_strong()


def list_item_muted() -> str:
    return _t().list_item_muted()


def form_label_muted() -> str:
    return _t().form_label_muted()


def view_toggle_button() -> str:
    return _t().view_toggle_button()


def view_toggle_menu() -> str:
    return _t().view_toggle_menu()


def progress_dialog() -> str:
    return _t().progress_dialog()


# ---- Responsive layout metrics ----
# Base metrics are aligned with the previous hard-coded px constants.
_TILE_MIN_WIDTH_BASE_PX = 220
_TILE_GRID_SPACING_BASE_PX = 16
_POSTER_MIN_CARD_WIDTH_BASE_PX = 150
_POSTER_GRID_SPACING_BASE_PX = 13


def _p() -> DensityProfile:
    # Internal helper: returns current density profile.
    return get_profile(get_current_density_key())


def sidebar_width_px() -> int:
    p = _p()
    return scaled_int(
        SIDEBAR_WIDTH_PX,
        p.sidebar_width_scale,
        minimum=240,
        maximum=380,
    )


def tile_min_width_px() -> int:
    p = _p()
    return scaled_int(
        _TILE_MIN_WIDTH_BASE_PX,
        p.card_min_width_scale,
        minimum=170,
        maximum=340,
    )


def tile_grid_spacing_px() -> int:
    p = _p()
    return scaled_int(
        _TILE_GRID_SPACING_BASE_PX,
        p.grid_spacing_scale,
        minimum=10,
        maximum=28,
    )


def poster_min_card_width_px() -> int:
    p = _p()
    return scaled_int(
        _POSTER_MIN_CARD_WIDTH_BASE_PX,
        p.card_min_width_scale,
        minimum=110,
        maximum=280,
    )


def poster_grid_spacing_px() -> int:
    p = _p()
    return scaled_int(
        _POSTER_GRID_SPACING_BASE_PX,
        p.grid_spacing_scale,
        minimum=7,
        maximum=22,
    )
