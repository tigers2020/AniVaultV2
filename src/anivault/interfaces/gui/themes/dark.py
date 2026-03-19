"""Dark theme: current AniVault QSS palette."""

from anivault.interfaces.gui.themes.base import (
    FONT_BODY,
    FONT_CAPTION,
    FONT_FAMILY,
    FONT_LARGE_TITLE,
    FONT_STAT,
    FONT_SUBTITLE,
    FONT_TITLE,
    RADIUS_PX,
    ColorPalette,
)


class DarkTheme:
    """Dark theme with navy/blue palette."""

    def __init__(self, *, scale: float = 1.0) -> None:
        # `scale` is derived from responsive density.
        # It affects typography density (via root font-size) and metric values
        # (radius, spacing in QSS strings that use pixel-based radii).
        self._scale = float(scale)
        self._root_font_size_px = max(10, int(round(16 * self._scale)))
        self._radius_px = max(8, int(round(RADIUS_PX * self._scale)))
        self._button_radius_px = max(8, int(round(14 * self._scale)))
        self._input_radius_px = max(8, int(round(12 * self._scale)))
        self._frame_radius_px = max(8, int(round(16 * self._scale)))
        self._menu_outer_radius_px = max(8, int(round(12 * self._scale)))
        self._menu_item_radius_px = max(6, int(round(8 * self._scale)))
        self._progressbar_radius_px = max(6, int(round(10 * self._scale)))
        self._progressbar_chunk_radius_px = max(4, int(round(9 * self._scale)))

        self.palette = ColorPalette(
            bg="#0b1020",
            panel="#121933",
            panel2="#182243",
            border="#2b3766",
            border_subtle="rgba(43, 55, 102, 0.28)",
            text="#e8ecff",
            muted="#9aa7d3",
            accent="#7aa2ff",
            accent2="#73e0c1",
            warn="#ffb454",
            danger="#ff6b81",
            ok="#4ade80",
            input_bg="rgba(11, 16, 32, 0.82)",
            table_bg="rgba(24, 34, 67, 0.65)",
            header_bg="rgba(11, 16, 32, 0.45)",
            sidebar_bg="rgba(10, 15, 30, 0.9)",
            card_bg="rgba(24, 34, 67, 0.88)",
        )
        self.colors = self.palette.to_dict()

    def _c(self) -> dict[str, str]:
        return self.colors

    def global_stylesheet(self) -> str:
        c = self._c()
        return f"""
        QWidget {{
            background-color: {c["bg"]};
            color: {c["text"]};
            font-family: {FONT_FAMILY};
            font-size: {self._root_font_size_px}px;
        }}
        QMainWindow {{
            background-color: {c["bg"]};
        }}
        QFrame {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: {self._radius_px}px;
            color: {c["text"]};
        }}
        QLabel {{
            color: {c["text"]};
            border: none;
            background: transparent;
            font-family: {FONT_FAMILY};
            font-size: 0.92rem;
        }}
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["panel2"]}, stop:1 {c["panel"]});
            border: 1px solid {c["border"]};
            border-top-color: rgba(43, 55, 102, 0.45);
            border-left-color: rgba(43, 55, 102, 0.45);
            border-bottom-color: rgba(20, 28, 55, 0.95);
            border-right-color: rgba(20, 28, 55, 0.95);
            border-radius: {self._button_radius_px}px;
            color: {c["text"]};
            padding: 11px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(122, 162, 255, 0.18), stop:1 rgba(122, 162, 255, 0.08));
            border-color: rgba(122, 162, 255, 0.28);
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["panel"]}, stop:1 #0d1328);
            border-top-color: rgba(20, 28, 55, 0.95);
            border-left-color: rgba(20, 28, 55, 0.95);
            border-bottom-color: rgba(43, 55, 102, 0.45);
            border-right-color: rgba(43, 55, 102, 0.45);
            padding: 12px 14px 10px 14px;
        }}
        QPushButton#primary {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8fa8ff, stop:1 #6b82e8);
            color: #0a1022;
            border: none;
        }}
        QPushButton#primary:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9eb4ff, stop:1 #8e8cff);
            border: none;
        }}
        QPushButton#primary:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5c72d4, stop:1 #4a5fc7);
            padding: 12px 14px 10px 14px;
        }}
        QPushButton#success {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8ef5e5, stop:1 #5cc9b8);
            color: #07151a;
            border: none;
        }}
        QPushButton#success:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9ef9ea, stop:1 #91f0da);
            border: none;
        }}
        QPushButton#success:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4ab5a5, stop:1 #3da898);
            padding: 12px 14px 10px 14px;
        }}
        QPushButton#warn {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 180, 84, 0.22), stop:1 rgba(255, 180, 84, 0.1));
            border: 1px solid rgba(255, 180, 84, 0.3);
            border-top-color: rgba(255, 180, 84, 0.38);
            border-left-color: rgba(255, 180, 84, 0.38);
            border-bottom-color: rgba(255, 180, 84, 0.22);
            border-right-color: rgba(255, 180, 84, 0.22);
            color: #ffd697;
        }}
        QPushButton#warn:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 180, 84, 0.08), stop:1 rgba(255, 180, 84, 0.18));
            padding: 12px 14px 10px 14px;
        }}
        QPushButton#danger {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 107, 129, 0.22), stop:1 rgba(255, 107, 129, 0.1));
            border: 1px solid rgba(255, 107, 129, 0.3);
            border-top-color: rgba(255, 107, 129, 0.38);
            border-left-color: rgba(255, 107, 129, 0.38);
            border-bottom-color: rgba(255, 107, 129, 0.22);
            border-right-color: rgba(255, 107, 129, 0.22);
            color: #ffc0cb;
        }}
        QPushButton#danger:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 107, 129, 0.08), stop:1 rgba(255, 107, 129, 0.18));
            padding: 12px 14px 10px 14px;
        }}
        QToolButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["panel2"]}, stop:1 {c["panel2"]});
            border: 1px solid {c["border"]};
            border-top-color: rgba(43, 55, 102, 0.45);
            border-left-color: rgba(43, 55, 102, 0.45);
            border-bottom-color: rgba(20, 28, 55, 0.95);
            border-right-color: rgba(20, 28, 55, 0.95);
            border-radius: {self._button_radius_px}px;
            color: {c["text"]};
            padding: 11px 14px;
            font-weight: 600;
        }}
        QToolButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(122, 162, 255, 0.18), stop:1 rgba(122, 162, 255, 0.08));
            border-color: rgba(122, 162, 255, 0.28);
        }}
        QToolButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["panel"]}, stop:1 #0d1328);
            border-top-color: rgba(20, 28, 55, 0.95);
            border-left-color: rgba(20, 28, 55, 0.95);
            border-bottom-color: rgba(43, 55, 102, 0.45);
            border-right-color: rgba(43, 55, 102, 0.45);
            padding: 12px 14px 10px 14px;
        }}
        QToolButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8fa8ff, stop:1 #6b82e8);
            color: #0a1022;
            border: none;
        }}
        QToolButton:checked:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9eb4ff, stop:1 #8e8cff);
            border: none;
        }}
        QLineEdit, QComboBox, QPlainTextEdit {{
            background-color: {c["input_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._input_radius_px}px;
            color: {c["text"]};
            padding: 11px 12px;
            font-family: {FONT_FAMILY};
            font-size: 0.92rem;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QTableWidget, QTableView {{
            background-color: {c["table_bg"]};
            gridline-color: rgba(43, 55, 102, 0.7);
            color: {c["text"]};
            border: none;
        }}
        QHeaderView::section {{
            background-color: {c["header_bg"]};
            color: {c["muted"]};
            padding: 12px 14px;
            font-family: {FONT_FAMILY};
            font-size: 0.86rem;
            font-weight: 600;
        }}
        QFrame#sidebar_pipeline_card QLabel {{
            color: {c["text"]};
            background: transparent;
            border: none;
        }}
    """

    def main_bg(self) -> str:
        return f"background-color: {self._c()['bg']};"

    def scroll_area_transparent(self) -> str:
        return "QScrollArea { border: none; background: transparent; }"

    def sidebar(self) -> str:
        c = self._c()
        return f"""
        QWidget#sidebar {{
            background-color: {c["sidebar_bg"]};
            border-right: 1px solid {c["border"]};
        }}
    """

    def sidebar_nav_title(self) -> str:
        c = self._c()
        return (
            f"color: {c['muted']}; font-family: {FONT_FAMILY}; font-size: 0.76rem; font-weight: 600; "
            "text-transform: uppercase; letter-spacing: 0.08em; margin: 18px 10px 10px; "
            "background: transparent; border: none;"
        )

    def sidebar_card(self) -> str:
        c = self._c()
        return f"""
        QFrame {{
            margin-top: 18px;
            padding: 14px;
            border: 1px solid {c["border"]};
            border-radius: {self._frame_radius_px}px;
            background-color: {c["card_bg"]};
        }}
    """

    def sidebar_card_title(self) -> str:
        c = self._c()
        return f"{FONT_TITLE} font-size: 0.95rem; margin: 0 0 8px; color: {c['text']}; background: transparent; border: none;"

    def sidebar_footer(self) -> str:
        c = self._c()
        return f"""
        QFrame {{
            padding: 14px;
            border: 1px solid {c["border"]};
            border-radius: {self._frame_radius_px}px;
            background-color: {c["card_bg"]};
        }}
    """

    def sidebar_footer_value(self) -> str:
        c = self._c()
        return f"margin-top: 6px; font-family: {FONT_FAMILY}; font-size: 0.92rem; font-weight: 700; color: {c['text']}; background: transparent; border: none;"

    def topbar_title(self) -> str:
        c = self._c()
        return f"{FONT_LARGE_TITLE} margin: 0; color: {c['text']}; background: transparent; border: none;"

    def topbar_desc(self) -> str:
        c = self._c()
        return f"margin-top: 6px; {FONT_SUBTITLE} color: {c['muted']}; background: transparent; border: none;"

    def label_muted(self) -> str:
        c = self._c()
        return f"color: {c['muted']}; {FONT_BODY} font-size: 0.84rem; background: transparent; border: none;"

    def label_stat(self) -> str:
        c = self._c()
        return f"color: {c['muted']}; {FONT_STAT} margin: 0 0 8px 0; background: transparent; border: none;"

    def label_title(self) -> str:
        c = self._c()
        return f"{FONT_TITLE} font-size: 1rem; color: {c['text']}; background: transparent; border: none;"

    def line_edit(self) -> str:
        c = self._c()
        return f"""
        QLineEdit {{
            background-color: {c["input_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._input_radius_px}px;
            color: {c["text"]};
            padding: 11px 12px;
        }}
    """

    def combo_box(self) -> str:
        c = self._c()
        return f"""
        QComboBox {{
            background-color: {c["input_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._input_radius_px}px;
            color: {c["text"]};
            padding: 11px 12px;
            min-height: 20px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
    """

    def pill(self, color: str = "blue") -> str:
        styles = {
            "blue": "background: rgba(122, 162, 255, 0.14); color: #bfd0ff; border: 1px solid rgba(122, 162, 255, 0.25);",
            "green": "background: rgba(74, 222, 128, 0.14); color: #b9f6ca; border: 1px solid rgba(74, 222, 128, 0.25);",
            "yellow": "background: rgba(255, 180, 84, 0.14); color: #ffd697; border: 1px solid rgba(255, 180, 84, 0.25);",
            "red": "background: rgba(255, 107, 129, 0.14); color: #ffc0cb; border: 1px solid rgba(255, 107, 129, 0.25);",
        }
        base = styles.get(color, styles["blue"])
        return f"padding: 6px 10px; border-radius: 999px; font-size: 0.78rem; {base}"

    def step_index_label(self) -> str:
        return "color: #ffffff; font-size: 0.78rem; font-weight: 700; background: transparent;"

    def badge_label(self, size: int) -> str:
        return f"color: #08101f; font-weight: 800; font-size: {max(14, size // 2)}px; background: transparent; border: none;"

    def nav_item(self) -> str:
        c = self._c()
        return f"""
        QPushButton {{
            width: 100%;
            text-align: left;
            padding: 13px 14px;
            border-radius: {self._button_radius_px}px;
            background: transparent;
            border: 1px solid transparent;
            color: {c["text"]};
            font-family: {FONT_FAMILY};
            font-size: 0.95rem;
            font-weight: 500;
        }}
        QPushButton:hover, QPushButton:checked {{
            background: rgba(122, 162, 255, 0.12);
            border-color: rgba(122, 162, 255, 0.28);
        }}
    """

    def step_row_title(self) -> str:
        c = self._c()
        return f"color: {c['text']}; {FONT_TITLE} font-size: 0.9rem; background: transparent; border: none;"

    def step_row_text(self) -> str:
        c = self._c()
        return f"color: {c['text']}; {FONT_BODY} font-size: 0.84rem; background: transparent; border: none;"

    def brand_title(self) -> str:
        return f"{FONT_TITLE} font-size: 1.02rem; margin: 0; background: transparent; border: none;"

    def brand_subtitle(self) -> str:
        return f"{FONT_SUBTITLE} font-size: 0.84rem; margin-top: 4px; background: transparent; border: none;"

    def stat_card(self) -> str:
        c = self._c()
        return f"""
        QFrame#stat_card {{
            background-color: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._radius_px}px;
        }}
        QFrame#stat_card QLabel {{
            background: transparent;
            border: none;
        }}
    """

    def stat_card_value(self) -> str:
        c = self._c()
        return f"font-family: {FONT_FAMILY}; font-size: 1.6rem; font-weight: 800; color: {c['text']}; background: transparent; border: none; margin: 0;"

    def panel_header_title(self) -> str:
        return f"{FONT_TITLE} font-size: 1.05rem; margin: 0; background: transparent; border: none;"

    def panel_header_desc(self) -> str:
        return f"{FONT_SUBTITLE} margin-top: 6px; background: transparent; border: none;"

    def path_box(self) -> str:
        c = self._c()
        return f"""
        QLabel {{
            background-color: {c["input_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._input_radius_px}px;
            padding: 10px;
            font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
            color: {c["text"]};
            font-size: 0.82rem;
        }}
    """

    def poster_card(self) -> str:
        c = self._c()
        return f"""
        QFrame {{
            background-color: {c["panel2"]};
            border: 1px solid {c["border"]};
            border-radius: {self._frame_radius_px}px;
        }}
    """

    def poster_card_image(self) -> str:
        c = self._c()
        return f"background-color: {c['input_bg']}; color: {c['muted']};"

    def poster_card_title(self) -> str:
        return f"{FONT_TITLE} font-size: 1rem; margin: 0; background: transparent; border: none;"

    def poster_card_meta(self) -> str:
        return f"{FONT_BODY} font-size: 0.88rem; line-height: 1.45; background: transparent; border: none;"

    def card_panel(self) -> str:
        c = self._c()
        return f"""
        QFrame {{
            background-color: {c["card_bg"]};
            border: 1px solid {c["border"]};
            border-radius: {self._radius_px}px;
        }}
    """

    def list_item(self) -> str:
        c = self._c()
        return f"""
        QWidget {{
            background-color: {c["panel2"]};
            border: 1px solid {c["border"]};
            border-radius: {self._button_radius_px}px;
        }}
    """

    def list_item_strong(self) -> str:
        c = self._c()
        return f"{FONT_TITLE} font-size: 0.96rem; margin-bottom: 6px; color: {c['text']}; background: transparent; border: none;"

    def list_item_muted(self) -> str:
        return f"{FONT_BODY} color: {self._c()['muted']}; background: transparent; border: none;"

    def form_label_muted(self) -> str:
        c = self._c()
        return f"{FONT_CAPTION} color: {c['muted']}; background: transparent; border: none;"

    def view_toggle_button(self) -> str:
        c = self._c()
        return f"""
        QToolButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["panel2"]}, stop:1 {c["panel2"]});
            border: 1px solid {c["border"]};
            border-top-color: rgba(43, 55, 102, 0.45);
            border-left-color: rgba(43, 55, 102, 0.45);
            border-bottom-color: rgba(20, 28, 55, 0.95);
            border-right-color: rgba(20, 28, 55, 0.95);
            border-radius: {self._button_radius_px}px;
            color: {c["text"]};
            padding: 11px 14px;
            font-weight: 600;
            font-size: 0.88rem;
        }}
        QToolButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(122, 162, 255, 0.18), stop:1 rgba(122, 162, 255, 0.08));
            border-color: rgba(122, 162, 255, 0.28);
        }}
        QToolButton:checked {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8fa8ff, stop:1 #6b82e8);
            color: #0a1022;
            border: none;
        }}
        QToolButton:checked:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9eb4ff, stop:1 #8e8cff);
            border: none;
        }}
        QToolButton::menu-indicator {{
            width: 16px;
        }}
    """

    def view_toggle_menu(self) -> str:
        c = self._c()
        return f"""
        QMenu {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: {self._menu_outer_radius_px}px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 10px 24px;
            border-radius: {self._menu_item_radius_px}px;
            color: {c["text"]};
        }}
        QMenu::item:selected {{
            background-color: rgba(122, 162, 255, 0.18);
        }}
        QMenu::item:disabled {{
            color: {c["muted"]};
        }}
        QMenu::separator {{
            height: 1px;
            background: {c["border"]};
            margin: 6px 8px;
        }}
    """

    def progress_dialog(self) -> str:
        c = self._c()
        return f"""
        QProgressDialog {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: {self._radius_px}px;
            color: {c["text"]};
        }}
        QProgressDialog QLabel {{
            color: {c["text"]};
            font-size: 0.95rem;
        }}
        QProgressBar {{
            border: 1px solid {c["border"]};
            border-radius: {self._progressbar_radius_px}px;
            text-align: center;
            background-color: {c["input_bg"]};
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c["accent"]}, stop:1 #8e8cff);
            border-radius: {self._progressbar_chunk_radius_px}px;
        }}
    """
