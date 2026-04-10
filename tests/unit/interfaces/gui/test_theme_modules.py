from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

from anivault.interfaces.gui import theme as theme_module
from anivault.interfaces.gui.themes import responsive as responsive_module
from anivault.interfaces.gui.themes.dark import DarkTheme

themes_module = importlib.import_module("anivault.interfaces.gui.themes")


class _FakeTheme:
    colors = {"bg": "#000"}

    def __getattr__(self, name: str):
        if name == "frame_radius_px":
            return lambda: 17
        if name == "pill":
            return lambda color="blue": f"pill:{color}"
        if name == "badge_label":
            return lambda size: f"badge:{size}"
        return lambda: name


def test_theme_module_wrappers_and_metrics(monkeypatch) -> None:
    monkeypatch.setattr(theme_module, "_t", lambda: _FakeTheme())
    monkeypatch.setattr(
        theme_module,
        "_p",
        lambda: SimpleNamespace(
            scale=1.1,
            sidebar_width_scale=1.0,
            card_min_width_scale=1.0,
            grid_spacing_scale=1.0,
        ),
    )

    assert theme_module.__getattr__("COLORS") == {"bg": "#000"}
    assert theme_module.global_stylesheet() == "global_stylesheet"
    assert theme_module.main_bg() == "main_bg"
    assert theme_module.scroll_area_transparent() == "scroll_area_transparent"
    assert theme_module.sidebar() == "sidebar"
    assert theme_module.sidebar_nav_title() == "sidebar_nav_title"
    assert theme_module.sidebar_card() == "sidebar_card"
    assert theme_module.sidebar_card_title() == "sidebar_card_title"
    assert theme_module.sidebar_footer() == "sidebar_footer"
    assert theme_module.sidebar_footer_value() == "sidebar_footer_value"
    assert theme_module.topbar_title() == "topbar_title"
    assert theme_module.topbar_desc() == "topbar_desc"
    assert theme_module.label_muted() == "label_muted"
    assert theme_module.label_stat() == "label_stat"
    assert theme_module.label_title() == "label_title"
    assert theme_module.line_edit() == "line_edit"
    assert theme_module.combo_box() == "combo_box"
    assert theme_module.pill("green") == "pill:green"
    assert theme_module.step_index_label() == "step_index_label"
    assert theme_module.badge_label(12) == "badge:12"
    assert theme_module.nav_item() == "nav_item"
    assert theme_module.step_row_title() == "step_row_title"
    assert theme_module.step_row_text() == "step_row_text"
    assert theme_module.brand_title() == "brand_title"
    assert theme_module.brand_subtitle() == "brand_subtitle"
    assert theme_module.stat_card() == "stat_card"
    assert theme_module.stat_card_value() == "stat_card_value"
    assert theme_module.panel_header_title() == "panel_header_title"
    assert theme_module.panel_header_desc() == "panel_header_desc"
    assert theme_module.path_box() == "path_box"
    assert theme_module.poster_card() == "poster_card"
    assert theme_module.frame_radius_px() == 17
    assert theme_module.poster_card_image() == "poster_card_image"
    assert theme_module.poster_card_title() == "poster_card_title"
    assert theme_module.poster_card_meta() == "poster_card_meta"
    assert theme_module.content_view_text_panel_overlay() == "content_view_text_panel_overlay"
    assert theme_module.card_panel() == "card_panel"
    assert theme_module.list_item() == "list_item"
    assert theme_module.list_item_strong() == "list_item_strong"
    assert theme_module.list_item_muted() == "list_item_muted"
    assert theme_module.form_label_muted() == "form_label_muted"
    assert theme_module.view_toggle_button() == "view_toggle_button"
    assert theme_module.view_toggle_menu() == "view_toggle_menu"
    assert theme_module.progress_dialog() == "progress_dialog"
    assert theme_module.sidebar_width_px() > 0
    assert theme_module.poster_min_card_width_px() > 0
    assert theme_module.poster_grid_spacing_px() > 0
    assert theme_module.layout_spacing_md() > 0
    assert theme_module.layout_spacing_lg() > 0
    assert theme_module.layout_main_padding() > 0
    assert theme_module.page_section_gap_px() > 0
    assert theme_module.card_body_padding_px() > 0
    assert theme_module.inline_control_gap_px() > 0
    assert theme_module.compact_gap_px() > 0
    assert theme_module.panel_header_padding_px() > 0
    assert theme_module.panel_header_bottom_gap_px() > 0
    assert theme_module.panel_header_stack_gap_px() > 0
    assert theme_module.sidebar_padding_px() > 0
    assert theme_module.topbar_bottom_gap_px() > 0
    assert theme_module.result_list_panel_min_width_px() > 0
    assert theme_module.result_list_panel_max_width_px() > 0
    assert theme_module.details_pane_min_width_px() > 0
    assert theme_module.details_pane_max_width_px() > 0
    assert theme_module.details_pane_default_width_px() > 0
    assert theme_module.result_splitter_main_width_px() > 0
    assert theme_module.settings_card_body_padding_px() > 0
    assert theme_module.settings_row_gap_px() > 0
    assert theme_module.settings_section_gap_px() > 0
    assert theme_module.settings_page_section_gap_px() > 0
    assert theme_module.settings_page_grid_gap_px() > 0


def test_theme_registry_density_and_persistence(tmp_path, monkeypatch) -> None:
    class FakeTheme:
        def __init__(self, *, scale: float = 1.0) -> None:
            self.scale = scale
            self.colors = {"scale": str(scale)}

    callbacks: list[str] = []
    monkeypatch.setattr(themes_module, "_THEMES", {"dark": FakeTheme, "light": FakeTheme})
    monkeypatch.setattr(themes_module._registry, "themes", {"dark": FakeTheme, "light": FakeTheme})
    monkeypatch.setattr(themes_module._registry, "current_theme", None)
    monkeypatch.setattr(themes_module._registry, "current_theme_name", "dark")
    monkeypatch.setattr(themes_module._registry, "current_density_key", "standard")
    monkeypatch.setattr(
        themes_module._registry,
        "on_color_theme_changed",
        [lambda: callbacks.append("theme")],
    )
    monkeypatch.setattr(
        themes_module._registry,
        "on_density_changed",
        [lambda: callbacks.append("density")],
    )
    monkeypatch.setattr(themes_module, "get_profile", lambda key: SimpleNamespace(scale=1.25))
    monkeypatch.setattr(themes_module, "choose_density_key", lambda width, height: "compact")

    assert themes_module.list_themes() == ["dark", "light"]
    missing = themes_module.get_theme("missing")
    assert missing.__class__.__name__ in {"DarkTheme", "FakeTheme"}
    current = themes_module.get_current_theme()
    assert current.scale == 1.25
    assert themes_module.get_current_theme_name() == "dark"

    themes_module.set_current_theme("light")
    themes_module.set_responsive_density_key("compact")
    assert callbacks == ["theme", "density"]
    assert (
        themes_module.set_responsive_density_for_size(width=800, height=600, notify=False)
        == "compact"
    )

    theme_file = tmp_path / "theme.json"
    monkeypatch.setattr(themes_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(themes_module, "CONFIG_FILE", theme_file)
    themes_module.save_theme("light")
    assert "light" in theme_file.read_text(encoding="utf-8")
    themes_module.load_saved_theme()


def test_save_theme_preserves_nested_settings_structure(tmp_path, monkeypatch) -> None:
    theme_file = tmp_path / "config.json"
    theme_file.write_text(
        json.dumps(
            {
                "theme": "dark",
                "path_rules": {
                    "target_root": "F:/Library",
                    "path_template": "{target}\\{title}",
                },
                "parse_tmdb": {
                    "ignore_tokens": "x264",
                    "season_folder_format": "Season{season:02}",
                },
                "scan_build": {
                    "source_path": "F:/Anime",
                    "auto_scan_on_first_show": True,
                },
                "ui_state": {
                    "pipeline_results": {
                        "view_key": "icon_m",
                        "selected_index": 2,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(themes_module, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(themes_module, "CONFIG_FILE", theme_file)

    themes_module.save_theme("light")

    saved = json.loads(theme_file.read_text(encoding="utf-8"))
    assert saved["theme"] == "light"
    assert isinstance(saved["path_rules"], dict)
    assert isinstance(saved["parse_tmdb"], dict)
    assert isinstance(saved["scan_build"], dict)
    assert isinstance(saved["ui_state"], dict)
    assert saved["path_rules"]["target_root"] == "F:/Library"
    assert saved["scan_build"]["source_path"] == "F:/Anime"


def test_responsive_helpers_choose_profiles_and_bounds() -> None:
    assert responsive_module.choose_density_key(width=100, height=100) == "compact"
    assert responsive_module.choose_density_key(width=1280, height=768) in {
        "standard",
        "expanded",
        "spacious",
    }
    assert responsive_module.get_profile("compact").key == "compact"
    assert responsive_module.clamp_int(5.6, minimum=1, maximum=5) == 5
    assert responsive_module.scaled_int(10, 1.5, minimum=12, maximum=20) == 15
    assert responsive_module.scaled_int(10, 0.1, minimum=4) == 4


def test_dark_theme_public_methods_return_strings() -> None:
    theme = DarkTheme(scale=1.1)

    outputs = [
        theme.global_stylesheet(),
        theme.main_bg(),
        theme.scroll_area_transparent(),
        theme.sidebar(),
        theme.sidebar_nav_title(),
        theme.sidebar_card(),
        theme.sidebar_card_title(),
        theme.sidebar_footer(),
        theme.sidebar_footer_value(),
        theme.topbar_title(),
        theme.topbar_desc(),
        theme.label_muted(),
        theme.label_stat(),
        theme.label_title(),
        theme.line_edit(),
        theme.combo_box(),
        theme.pill(),
        theme.pill("green"),
        theme.step_index_label(),
        theme.badge_label(14),
        theme.nav_item(),
        theme.step_row_title(),
        theme.step_row_text(),
        theme.brand_title(),
        theme.brand_subtitle(),
        theme.stat_card(),
        theme.stat_card_value(),
        theme.panel_header_title(),
        theme.panel_header_desc(),
        theme.path_box(),
        theme.poster_card(),
        theme.poster_card_image(),
        theme.poster_card_title(),
        theme.poster_card_meta(),
        theme.content_view_text_panel_overlay(),
        theme.card_panel(),
        theme.list_item(),
        theme.list_item_strong(),
        theme.list_item_muted(),
        theme.form_label_muted(),
        theme.view_toggle_button(),
        theme.view_toggle_menu(),
        theme.progress_dialog(),
    ]

    assert all(isinstance(value, str) and value for value in outputs)
    assert theme.frame_radius_px() >= 8
