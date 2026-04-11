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
    "layout_spacing_sm_px",
    "layout_spacing_xs_px",
    "layout_main_padding",
    "page_section_gap_px",
    "card_body_padding_px",
    "inline_control_gap_px",
    "compact_gap_px",
    "panel_header_padding_px",
    "panel_header_bottom_gap_px",
    "panel_header_stack_gap_px",
    "sidebar_padding_px",
    "topbar_bottom_gap_px",
    "result_list_panel_min_width_px",
    "result_list_panel_max_width_px",
    "details_pane_min_width_px",
    "details_pane_max_width_px",
    "details_pane_default_width_px",
    "result_splitter_main_width_px",
    "settings_card_body_padding_px",
    "settings_row_gap_px",
    "settings_section_gap_px",
    "settings_page_section_gap_px",
    "settings_page_grid_gap_px",
    "settings_tab_content_margins_px",
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


def layout_spacing_sm_px() -> int:
    """Row gaps for path rows, pipeline steps, execution action bars."""
    profile = _p()
    return scaled_int(10, profile.grid_spacing_scale, minimum=8, maximum=14)


def layout_spacing_xs_px() -> int:
    """Dense horizontal gaps (view toggles, pill row offsets)."""
    profile = _p()
    return scaled_int(8, profile.grid_spacing_scale, minimum=6, maximum=12)


def layout_main_padding() -> int:
    profile = _p()
    return scaled_int(26, profile.scale, minimum=18, maximum=36)


def page_section_gap_px() -> int:
    profile = _p()
    return scaled_int(18, profile.grid_spacing_scale, minimum=12, maximum=28)


def card_body_padding_px() -> int:
    profile = _p()
    return scaled_int(18, profile.scale, minimum=14, maximum=28)


def inline_control_gap_px() -> int:
    profile = _p()
    return scaled_int(12, profile.grid_spacing_scale, minimum=8, maximum=18)


def compact_gap_px() -> int:
    profile = _p()
    return scaled_int(6, profile.grid_spacing_scale, minimum=4, maximum=10)


def panel_header_padding_px() -> int:
    profile = _p()
    return scaled_int(18, profile.scale, minimum=14, maximum=28)


def panel_header_bottom_gap_px() -> int:
    profile = _p()
    return scaled_int(12, profile.grid_spacing_scale, minimum=8, maximum=18)


def panel_header_stack_gap_px() -> int:
    profile = _p()
    return scaled_int(6, profile.grid_spacing_scale, minimum=4, maximum=10)


def sidebar_padding_px() -> int:
    profile = _p()
    return scaled_int(20, profile.scale, minimum=16, maximum=30)


def topbar_bottom_gap_px() -> int:
    profile = _p()
    return scaled_int(18, profile.grid_spacing_scale, minimum=12, maximum=24)


def result_list_panel_min_width_px() -> int:
    profile = _p()
    return scaled_int(280, profile.scale, minimum=240, maximum=360)


def result_list_panel_max_width_px() -> int:
    profile = _p()
    return scaled_int(420, profile.scale, minimum=360, maximum=520)


def details_pane_min_width_px() -> int:
    profile = _p()
    return scaled_int(320, profile.scale, minimum=280, maximum=420)


def details_pane_max_width_px() -> int:
    profile = _p()
    return scaled_int(500, profile.scale, minimum=420, maximum=620)


def details_pane_default_width_px() -> int:
    profile = _p()
    return scaled_int(360, profile.scale, minimum=300, maximum=440)


def result_splitter_main_width_px() -> int:
    profile = _p()
    return scaled_int(980, profile.scale, minimum=760, maximum=1280)


def settings_card_body_padding_px() -> int:
    return card_body_padding_px()


def settings_row_gap_px() -> int:
    return inline_control_gap_px()


def settings_section_gap_px() -> int:
    profile = _p()
    return scaled_int(14, profile.grid_spacing_scale, minimum=10, maximum=22)


def settings_page_section_gap_px() -> int:
    return page_section_gap_px()


def settings_page_grid_gap_px() -> int:
    profile = _p()
    return scaled_int(16, profile.grid_spacing_scale, minimum=12, maximum=24)


def settings_tab_content_margins_px() -> int:
    """Inset inside each settings tab scroll viewport (below tab bar)."""
    profile = _p()
    return scaled_int(12, profile.scale, minimum=8, maximum=20)
