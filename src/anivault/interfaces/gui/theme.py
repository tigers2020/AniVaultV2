"""Theme: single source for all QSS. Python constants + style getters."""

# From gui.html :root — var(--border)=#2b3766, 테이블/path는 rgba(43,55,102,0.7)
# Typography: 타이틀 / 서브타이틀 / 본문 각각 고유 글꼴·크기
FONT_FAMILY = "Segoe UI, Malgun Gothic, Apple SD Gothic Neo, sans-serif"
FONT_TITLE = f"font-family: {FONT_FAMILY}; font-size: 1.12rem; font-weight: 700;"
FONT_SUBTITLE = f"font-family: {FONT_FAMILY}; font-size: 0.9rem; font-weight: 500;"
FONT_BODY = f"font-family: {FONT_FAMILY}; font-size: 0.92rem; font-weight: 400;"
FONT_CAPTION = f"font-family: {FONT_FAMILY}; font-size: 0.82rem; font-weight: 400;"
FONT_LARGE_TITLE = f"font-family: {FONT_FAMILY}; font-size: 1.5rem; font-weight: 700;"
FONT_STAT = f"font-family: {FONT_FAMILY}; font-size: 0.86rem; font-weight: 500;"

COLORS = {
    "bg": "#0b1020",
    "panel": "#121933",
    "panel2": "#182243",
    "border": "#2b3766",
    "border_subtle": "rgba(43, 55, 102, 0.28)",
    "text": "#e8ecff",
    "muted": "#9aa7d3",
    "accent": "#7aa2ff",
    "accent2": "#73e0c1",
    "warn": "#ffb454",
    "danger": "#ff6b81",
    "ok": "#4ade80",
}
RADIUS_PX = 18
SIDEBAR_WIDTH_PX = 260


def _c() -> dict[str, str]:
    return COLORS


# ---------------------------------------------------------------------------
# Global (app-level)
# ---------------------------------------------------------------------------

def global_stylesheet() -> str:
    """Build QSS string from COLORS and RADIUS. No box-shadow (use Effect)."""
    c = _c()
    return f"""
        QWidget {{
            background-color: {c["bg"]};
            color: {c["text"]};
            font-family: {FONT_FAMILY};
        }}
        QMainWindow {{
            background-color: {c["bg"]};
        }}
        QFrame {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_PX}px;
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
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: 14px;
            color: {c["text"]};
            padding: 11px 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: rgba(122, 162, 255, 0.12);
            border-color: rgba(122, 162, 255, 0.28);
        }}
        QPushButton#primary {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c["accent"]}, stop:1 #8e8cff);
            color: #0a1022;
            border: none;
        }}
        QPushButton#success {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c["accent2"]}, stop:1 #91f0da);
            color: #07151a;
            border: none;
        }}
        QPushButton#warn {{
            background-color: rgba(255, 180, 84, 0.14);
            border: 1px solid rgba(255, 180, 84, 0.3);
            color: #ffd697;
        }}
        QPushButton#danger {{
            background-color: rgba(255, 107, 129, 0.14);
            border: 1px solid rgba(255, 107, 129, 0.3);
            color: #ffc0cb;
        }}
        QLineEdit, QComboBox, QPlainTextEdit {{
            background-color: rgba(11, 16, 32, 0.82);
            border: 1px solid {c["border"]};
            border-radius: 12px;
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
            background-color: rgba(24, 34, 67, 0.65);
            gridline-color: rgba(43, 55, 102, 0.7);
            color: {c["text"]};
            border: none;
        }}
        QHeaderView::section {{
            background-color: rgba(11, 16, 32, 0.45);
            color: {c["muted"]};
            padding: 12px 14px;
            font-family: {FONT_FAMILY};
            font-size: 0.86rem;
            font-weight: 600;
        }}
    """


# ---------------------------------------------------------------------------
# Layout / shell
# ---------------------------------------------------------------------------

def main_bg() -> str:
    return f"background-color: {_c()['bg']};"


def scroll_area_transparent() -> str:
    return "QScrollArea { border: none; background: transparent; }"


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def sidebar() -> str:
    c = _c()
    return f"""
        QWidget {{
            background-color: rgba(10, 15, 30, 0.9);
            border-right: 1px solid {c["border"]};
        }}
    """


def sidebar_nav_title() -> str:
    c = _c()
    return (
        f"color: {c['muted']}; font-family: {FONT_FAMILY}; font-size: 0.76rem; font-weight: 600; "
        "text-transform: uppercase; letter-spacing: 0.08em; margin: 18px 10px 10px; "
        "background: transparent; border: none;"
    )


def sidebar_card() -> str:
    c = _c()
    return f"""
        QFrame {{
            margin-top: 18px;
            padding: 14px;
            border: 1px solid {c["border"]};
            border-radius: 16px;
            background-color: rgba(24, 34, 67, 0.88);
        }}
    """


def sidebar_card_title() -> str:
    c = _c()
    return f"{FONT_TITLE} font-size: 0.95rem; margin: 0 0 8px; color: {c['text']}; background: transparent; border: none;"


def sidebar_footer() -> str:
    c = _c()
    return f"""
        QFrame {{
            padding: 14px;
            border: 1px solid {c["border"]};
            border-radius: 16px;
            background-color: rgba(24, 34, 67, 0.88);
        }}
    """


def sidebar_footer_value() -> str:
    c = _c()
    return f"margin-top: 6px; font-family: {FONT_FAMILY}; font-size: 0.92rem; font-weight: 700; color: {c['text']}; background: transparent; border: none;"


# ---------------------------------------------------------------------------
# Topbar
# ---------------------------------------------------------------------------

def topbar_title() -> str:
    c = _c()
    return f"{FONT_LARGE_TITLE} margin: 0; color: {c['text']}; background: transparent; border: none;"


def topbar_desc() -> str:
    c = _c()
    return f"margin-top: 6px; {FONT_SUBTITLE} color: {c['muted']}; background: transparent; border: none;"


# ---------------------------------------------------------------------------
# Atoms
# ---------------------------------------------------------------------------

def label_muted() -> str:
    c = _c()
    return f"color: {c['muted']}; {FONT_BODY} font-size: 0.84rem; background: transparent; border: none;"


def label_stat() -> str:
    c = _c()
    return f"color: {c['muted']}; {FONT_STAT} margin: 0 0 8px 0; background: transparent; border: none;"


def label_title() -> str:
    c = _c()
    return f"{FONT_TITLE} font-size: 1rem; color: {c['text']}; background: transparent; border: none;"


def line_edit() -> str:
    c = _c()
    return f"""
        QLineEdit {{
            background-color: rgba(11, 16, 32, 0.82);
            border: 1px solid {c["border"]};
            border-radius: 12px;
            color: {c["text"]};
            padding: 11px 12px;
        }}
    """


def combo_box() -> str:
    c = _c()
    return f"""
        QComboBox {{
            background-color: rgba(11, 16, 32, 0.82);
            border: 1px solid {c["border"]};
            border-radius: 12px;
            color: {c["text"]};
            padding: 11px 12px;
            min-height: 20px;
        }}
        QComboBox::drop-down {{
            border: none;
        }}
    """


def pill(color: str = "blue") -> str:
    styles = {
        "blue": "background: rgba(122, 162, 255, 0.14); color: #bfd0ff; border: 1px solid rgba(122, 162, 255, 0.25);",
        "green": "background: rgba(74, 222, 128, 0.14); color: #b9f6ca; border: 1px solid rgba(74, 222, 128, 0.25);",
        "yellow": "background: rgba(255, 180, 84, 0.14); color: #ffd697; border: 1px solid rgba(255, 180, 84, 0.25);",
        "red": "background: rgba(255, 107, 129, 0.14); color: #ffc0cb; border: 1px solid rgba(255, 107, 129, 0.25);",
    }
    base = styles.get(color, styles["blue"])
    return f"padding: 6px 10px; border-radius: 999px; font-size: 0.78rem; {base}"


def step_index_label() -> str:
    return "color: #091120; font-size: 0.78rem; font-weight: 700; background: transparent;"


def badge_label(size: int) -> str:
    return f"color: #08101f; font-weight: 800; font-size: {max(14, size // 2)}px; background: transparent; border: none;"


# ---------------------------------------------------------------------------
# Molecules
# ---------------------------------------------------------------------------

def nav_item() -> str:
    c = _c()
    return f"""
        QPushButton {{
            width: 100%;
            text-align: left;
            padding: 13px 14px;
            border-radius: 14px;
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


def step_row_text() -> str:
    c = _c()
    return f"color: {c['muted']}; {FONT_BODY} font-size: 0.84rem; background: transparent; border: none;"


def brand_title() -> str:
    return f"{FONT_TITLE} font-size: 1.02rem; margin: 0; background: transparent; border: none;"


def brand_subtitle() -> str:
    return f"{FONT_SUBTITLE} font-size: 0.84rem; margin-top: 4px; background: transparent; border: none;"


def stat_card() -> str:
    c = _c()
    return f"""
        QFrame#stat_card {{
            background-color: rgba(18, 25, 51, 0.88);
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_PX}px;
        }}
        QFrame#stat_card QLabel {{
            background: transparent;
            border: none;
        }}
    """


def stat_card_value() -> str:
    c = _c()
    return f"font-family: {FONT_FAMILY}; font-size: 1.6rem; font-weight: 800; color: {c['text']}; background: transparent; border: none; margin: 0;"


def panel_header_title() -> str:
    return f"{FONT_TITLE} font-size: 1.05rem; margin: 0; background: transparent; border: none;"


def panel_header_desc() -> str:
    return f"{FONT_SUBTITLE} margin-top: 6px; background: transparent; border: none;"


def path_box() -> str:
    """Path display style. Use QLabel.setWordWrap(True) in code for wrapping."""
    return """
        QLabel {
            background-color: rgba(11, 16, 32, 0.65);
            border: 1px solid rgba(43, 55, 102, 0.7);
            border-radius: 12px;
            padding: 10px;
            font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
            color: #d5ddff;
            font-size: 0.82rem;
        }
    """


def poster_card() -> str:
    c = _c()
    return f"""
        QFrame {{
            background-color: rgba(24, 34, 67, 0.92);
            border: 1px solid {c["border"]};
            border-radius: 16px;
        }}
    """


def poster_card_image() -> str:
    c = _c()
    return f"background-color: rgba(11, 16, 32, 0.82); color: {c['muted']};"


def poster_card_title() -> str:
    return f"{FONT_TITLE} font-size: 1rem; margin: 0; background: transparent; border: none;"


def poster_card_meta() -> str:
    return f"{FONT_BODY} font-size: 0.88rem; line-height: 1.45; background: transparent; border: none;"


# ---------------------------------------------------------------------------
# Organisms: cards and panels
# ---------------------------------------------------------------------------

def card_panel() -> str:
    c = _c()
    return f"""
        QFrame {{
            background-color: rgba(18, 25, 51, 0.88);
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_PX}px;
        }}
    """


def list_item() -> str:
    c = _c()
    return f"""
        QWidget {{
            background-color: rgba(24, 34, 67, 0.9);
            border: 1px solid {c["border"]};
            border-radius: 14px;
        }}
    """


def list_item_strong() -> str:
    c = _c()
    return f"{FONT_TITLE} font-size: 0.96rem; margin-bottom: 6px; color: {c['text']}; background: transparent; border: none;"


def list_item_muted() -> str:
    c = _c()
    return f"{FONT_BODY} color: {c['muted']}; background: transparent; border: none;"


def form_label_muted() -> str:
    c = _c()
    return f"{FONT_CAPTION} color: {c['muted']}; background: transparent; border: none;"


# ---------------------------------------------------------------------------
# View toggle bar
# ---------------------------------------------------------------------------

def view_toggle_button() -> str:
    c = _c()
    return f"""
        QToolButton {{
            background-color: rgba(24, 34, 67, 0.7);
            border: 1px solid {c["border"]};
            border-radius: 10px;
            color: {c["text"]};
            padding: 8px 12px;
            font-size: 0.88rem;
        }}
        QToolButton:hover {{
            background-color: rgba(122, 162, 255, 0.12);
            border-color: rgba(122, 162, 255, 0.28);
        }}
        QToolButton::menu-indicator {{
            width: 16px;
        }}
    """


def view_toggle_menu() -> str:
    c = _c()
    return f"""
        QMenu {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: 12px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 10px 24px;
            border-radius: 8px;
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


# ---------------------------------------------------------------------------
# Progress dialog
# ---------------------------------------------------------------------------

def progress_dialog() -> str:
    c = _c()
    return f"""
        QProgressDialog {{
            background-color: {c["panel"]};
            border: 1px solid {c["border"]};
            border-radius: {RADIUS_PX}px;
            color: {c["text"]};
        }}
        QProgressDialog QLabel {{
            color: {c["text"]};
            font-size: 0.95rem;
        }}
        QProgressBar {{
            border: 1px solid {c["border"]};
            border-radius: 10px;
            text-align: center;
            background-color: rgba(11, 16, 32, 0.82);
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c["accent"]}, stop:1 #8e8cff);
            border-radius: 9px;
        }}
    """
