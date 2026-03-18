"""Theme facade: delegates to themes package. Keeps existing import paths."""

from anivault.interfaces.gui.themes import get_current_theme
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
