"""Theme facade over the active theme instance and responsive metrics."""

from __future__ import annotations

from typing import Any

from anivault.constants.gui.theme import POSTER_GRID_SPACING_BASE_PX, POSTER_MIN_CARD_WIDTH_BASE_PX
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
)
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
    "frame_radius_px",
    "poster_card_image",
    "poster_card_title",
    "poster_card_meta",
    "content_view_text_panel_overlay",
    "card_panel",
    "list_item",
    "list_item_strong",
    "list_item_muted",
    "form_label_muted",
    "view_toggle_button",
    "view_toggle_menu",
    "progress_dialog",
    "sidebar_width_px",
    "poster_min_card_width_px",
    "poster_grid_spacing_px",
    "layout_spacing_md",
    "layout_spacing_lg",
    "layout_main_padding",
    "settings_card_body_padding_px",
    "settings_row_gap_px",
    "settings_section_gap_px",
    "settings_page_section_gap_px",
    "settings_page_grid_gap_px",
]


def _t() -> Any:
    return get_current_theme()


def _theme_str(name: str, *args: object) -> str:
    return str(getattr(_t(), name)(*args))


def _theme_int(name: str) -> int:
    return int(getattr(_t(), name)())


def __getattr__(name: str) -> Any:
    if name == "COLORS":
        return _t().colors
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def global_stylesheet() -> str:
    return _theme_str("global_stylesheet")


def main_bg() -> str:
    return _theme_str("main_bg")


def scroll_area_transparent() -> str:
    return _theme_str("scroll_area_transparent")


def sidebar() -> str:
    return _theme_str("sidebar")


def sidebar_nav_title() -> str:
    return _theme_str("sidebar_nav_title")


def sidebar_card() -> str:
    return _theme_str("sidebar_card")


def sidebar_card_title() -> str:
    return _theme_str("sidebar_card_title")


def sidebar_footer() -> str:
    return _theme_str("sidebar_footer")


def sidebar_footer_value() -> str:
    return _theme_str("sidebar_footer_value")


def topbar_title() -> str:
    return _theme_str("topbar_title")


def topbar_desc() -> str:
    return _theme_str("topbar_desc")


def label_muted() -> str:
    return _theme_str("label_muted")


def label_stat() -> str:
    return _theme_str("label_stat")


def label_title() -> str:
    return _theme_str("label_title")


def line_edit() -> str:
    return _theme_str("line_edit")


def combo_box() -> str:
    return _theme_str("combo_box")


def pill(color: str = "blue") -> str:
    return _theme_str("pill", color)


def step_index_label() -> str:
    return _theme_str("step_index_label")


def badge_label(size: int) -> str:
    return _theme_str("badge_label", size)


def nav_item() -> str:
    return _theme_str("nav_item")


def step_row_title() -> str:
    return _theme_str("step_row_title")


def step_row_text() -> str:
    return _theme_str("step_row_text")


def brand_title() -> str:
    return _theme_str("brand_title")


def brand_subtitle() -> str:
    return _theme_str("brand_subtitle")


def stat_card() -> str:
    return _theme_str("stat_card")


def stat_card_value() -> str:
    return _theme_str("stat_card_value")


def panel_header_title() -> str:
    return _theme_str("panel_header_title")


def panel_header_desc() -> str:
    return _theme_str("panel_header_desc")


def path_box() -> str:
    return _theme_str("path_box")


def poster_card() -> str:
    return _theme_str("poster_card")


def frame_radius_px() -> int:
    return _theme_int("frame_radius_px")


def poster_card_image() -> str:
    return _theme_str("poster_card_image")


def poster_card_title() -> str:
    return _theme_str("poster_card_title")


def poster_card_meta() -> str:
    return _theme_str("poster_card_meta")


def content_view_text_panel_overlay() -> str:
    return _theme_str("content_view_text_panel_overlay")


def card_panel() -> str:
    return _theme_str("card_panel")


def list_item() -> str:
    return _theme_str("list_item")


def list_item_strong() -> str:
    return _theme_str("list_item_strong")


def list_item_muted() -> str:
    return _theme_str("list_item_muted")


def form_label_muted() -> str:
    return _theme_str("form_label_muted")


def view_toggle_button() -> str:
    return _theme_str("view_toggle_button")


def view_toggle_menu() -> str:
    return _theme_str("view_toggle_menu")


def progress_dialog() -> str:
    return _theme_str("progress_dialog")


def _p() -> DensityProfile:
    return get_profile(get_current_density_key())


def sidebar_width_px() -> int:
    profile = _p()
    return scaled_int(
        SIDEBAR_WIDTH_PX,
        profile.sidebar_width_scale,
        minimum=240,
        maximum=380,
    )


def poster_min_card_width_px() -> int:
    profile = _p()
    return scaled_int(
        POSTER_MIN_CARD_WIDTH_BASE_PX,
        profile.card_min_width_scale,
        minimum=110,
        maximum=280,
    )


def poster_grid_spacing_px() -> int:
    profile = _p()
    return scaled_int(
        POSTER_GRID_SPACING_BASE_PX,
        profile.grid_spacing_scale,
        minimum=7,
        maximum=22,
    )


def layout_spacing_md() -> int:
    profile = _p()
    return scaled_int(16, profile.grid_spacing_scale, minimum=10, maximum=24)


def layout_spacing_lg() -> int:
    profile = _p()
    return scaled_int(18, profile.grid_spacing_scale, minimum=12, maximum=26)


def layout_main_padding() -> int:
    profile = _p()
    return scaled_int(26, profile.scale, minimum=18, maximum=36)


def settings_card_body_padding_px() -> int:
    profile = _p()
    return scaled_int(18, profile.scale, minimum=14, maximum=28)


def settings_row_gap_px() -> int:
    profile = _p()
    return scaled_int(10, profile.grid_spacing_scale, minimum=8, maximum=16)


def settings_section_gap_px() -> int:
    profile = _p()
    return scaled_int(14, profile.grid_spacing_scale, minimum=10, maximum=20)


def settings_page_section_gap_px() -> int:
    profile = _p()
    return scaled_int(14, profile.grid_spacing_scale, minimum=10, maximum=22)


def settings_page_grid_gap_px() -> int:
    profile = _p()
    return scaled_int(16, profile.grid_spacing_scale, minimum=12, maximum=24)
