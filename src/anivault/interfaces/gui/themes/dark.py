"""dark.py

다크 테마 QSS 팔레트.

Author: Pom Kim
"""

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
from anivault.interfaces.gui.themes.qss_fragments import qss_block, qss_blocks

DARK_THEME_PALETTE = ColorPalette(
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


class DarkTheme:
    """Dark theme with navy/blue palette."""

    PALETTE = DARK_THEME_PALETTE
    CONTENT_VIEW_TEXT_PANEL_OVERLAY_BG = "rgba(0, 0, 0, 0.75)"

    def __init__(self, *, scale: float = 1.0) -> None:
        """밀도 스케일과 팔레트·파생 픽셀 값을 초기화한다.

        Args:
            self: 이 인스턴스.
        scale: 반응형 밀도에서 온 배율.

        Returns:
            None.
        """
        # `scale` is derived from responsive density.
        # It affects typography density (via root font-size) and metric values
        # (radius, spacing in QSS strings that use pixel-based radii).
        self._scale = float(scale)
        self._root_font_size_pt = max(8, int(round(12 * self._scale)))
        self._radius_px = max(8, int(round(RADIUS_PX * self._scale)))
        self._button_radius_px = max(8, int(round(14 * self._scale)))
        self._input_radius_px = max(8, int(round(12 * self._scale)))
        self._frame_radius_px = max(8, int(round(16 * self._scale)))
        self._menu_outer_radius_px = max(8, int(round(12 * self._scale)))
        self._menu_item_radius_px = max(6, int(round(8 * self._scale)))
        self._progressbar_radius_px = max(6, int(round(10 * self._scale)))
        self._progressbar_chunk_radius_px = max(4, int(round(9 * self._scale)))

        self.palette = self.PALETTE
        self.colors = self.palette.to_dict()

    def _c(self) -> dict[str, str]:
        """색상 dict 별칭을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            colors dict.
        """
        return self.colors

    def global_stylesheet(self) -> str:
        """global stylesheet용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_blocks(
            qss_block(
                "QWidget",
                f"background-color: {c['bg']}",
                f"color: {c['text']}",
                f"font-family: {FONT_FAMILY}",
                f"font-size: {self._root_font_size_pt}pt",
            ),
            qss_block("QMainWindow", f"background-color: {c['bg']}"),
            qss_block(
                "QFrame",
                f"background-color: {c['panel']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._radius_px}px",
                f"color: {c['text']}",
            ),
            qss_block(
                "QLabel",
                f"color: {c['text']}",
                "border: none",
                "background: transparent",
                f"font-family: {FONT_FAMILY}",
                "font-size: 11pt",
            ),
            qss_block(
                "QPushButton",
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['panel2']}, stop:1 {c['panel']})",
                f"border: 1px solid {c['border']}",
                "border-top-color: rgba(43, 55, 102, 0.45)",
                "border-left-color: rgba(43, 55, 102, 0.45)",
                "border-bottom-color: rgba(20, 28, 55, 0.95)",
                "border-right-color: rgba(20, 28, 55, 0.95)",
                f"border-radius: {self._button_radius_px}px",
                f"color: {c['text']}",
                "padding: 11px 14px",
                "font-weight: 600",
            ),
            qss_block(
                "QPushButton:hover",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(122, 162, 255, 0.18), stop:1 rgba(122, 162, 255, 0.08))",
                "border-color: rgba(122, 162, 255, 0.28)",
            ),
            qss_block(
                "QPushButton:pressed",
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['panel']}, stop:1 #0d1328)",
                "border-top-color: rgba(20, 28, 55, 0.95)",
                "border-left-color: rgba(20, 28, 55, 0.95)",
                "border-bottom-color: rgba(43, 55, 102, 0.45)",
                "border-right-color: rgba(43, 55, 102, 0.45)",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QPushButton#primary",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8fa8ff, stop:1 #6b82e8)",
                "color: #0a1022",
                "border: none",
            ),
            qss_block(
                "QPushButton#primary:hover",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9eb4ff, stop:1 #8e8cff)",
                "border: none",
            ),
            qss_block(
                "QPushButton#primary:pressed",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5c72d4, stop:1 #4a5fc7)",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QPushButton#success",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8ef5e5, stop:1 #5cc9b8)",
                "color: #07151a",
                "border: none",
            ),
            qss_block(
                "QPushButton#success:hover",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9ef9ea, stop:1 #91f0da)",
                "border: none",
            ),
            qss_block(
                "QPushButton#success:pressed",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4ab5a5, stop:1 #3da898)",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QPushButton#warn",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 180, 84, 0.22), stop:1 rgba(255, 180, 84, 0.1))",
                "border: 1px solid rgba(255, 180, 84, 0.3)",
                "border-top-color: rgba(255, 180, 84, 0.38)",
                "border-left-color: rgba(255, 180, 84, 0.38)",
                "border-bottom-color: rgba(255, 180, 84, 0.22)",
                "border-right-color: rgba(255, 180, 84, 0.22)",
                "color: #ffd697",
            ),
            qss_block(
                "QPushButton#warn:pressed",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 180, 84, 0.08), stop:1 rgba(255, 180, 84, 0.18))",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QPushButton#danger",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 107, 129, 0.22), stop:1 rgba(255, 107, 129, 0.1))",
                "border: 1px solid rgba(255, 107, 129, 0.3)",
                "border-top-color: rgba(255, 107, 129, 0.38)",
                "border-left-color: rgba(255, 107, 129, 0.38)",
                "border-bottom-color: rgba(255, 107, 129, 0.22)",
                "border-right-color: rgba(255, 107, 129, 0.22)",
                "color: #ffc0cb",
            ),
            qss_block(
                "QPushButton#danger:pressed",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 107, 129, 0.08), stop:1 rgba(255, 107, 129, 0.18))",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QToolButton",
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['panel2']}, stop:1 {c['panel2']})",
                f"border: 1px solid {c['border']}",
                "border-top-color: rgba(43, 55, 102, 0.45)",
                "border-left-color: rgba(43, 55, 102, 0.45)",
                "border-bottom-color: rgba(20, 28, 55, 0.95)",
                "border-right-color: rgba(20, 28, 55, 0.95)",
                f"border-radius: {self._button_radius_px}px",
                f"color: {c['text']}",
                "padding: 11px 14px",
                "font-weight: 600",
            ),
            qss_block(
                "QToolButton:hover",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(122, 162, 255, 0.18), stop:1 rgba(122, 162, 255, 0.08))",
                "border-color: rgba(122, 162, 255, 0.28)",
            ),
            qss_block(
                "QToolButton:pressed",
                f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c['panel']}, stop:1 #0d1328)",
                "border-top-color: rgba(20, 28, 55, 0.95)",
                "border-left-color: rgba(20, 28, 55, 0.95)",
                "border-bottom-color: rgba(43, 55, 102, 0.45)",
                "border-right-color: rgba(43, 55, 102, 0.45)",
                "padding: 12px 14px 10px 14px",
            ),
            qss_block(
                "QToolButton:checked",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8fa8ff, stop:1 #6b82e8)",
                "color: #0a1022",
                "border: none",
            ),
            qss_block(
                "QToolButton:checked:hover",
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #9eb4ff, stop:1 #8e8cff)",
                "border: none",
            ),
            qss_block(
                "QLineEdit, QComboBox, QPlainTextEdit",
                f"background-color: {c['input_bg']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._input_radius_px}px",
                f"color: {c['text']}",
                "padding: 11px 12px",
                f"font-family: {FONT_FAMILY}",
                "font-size: 11pt",
            ),
            qss_block("QComboBox::drop-down", "border: none"),
            qss_block("QScrollArea", "border: none", "background: transparent"),
            qss_block(
                "QTableWidget, QTableView",
                f"background-color: {c['table_bg']}",
                "gridline-color: rgba(43, 55, 102, 0.7)",
                f"color: {c['text']}",
                "border: none",
            ),
            qss_block(
                "QHeaderView::section",
                f"background-color: {c['header_bg']}",
                f"color: {c['muted']}",
                "padding: 12px 14px",
                f"font-family: {FONT_FAMILY}",
                "font-size: 10pt",
                "font-weight: 600",
            ),
            qss_block(
                "QFrame#sidebar_pipeline_card QLabel",
                f"color: {c['text']}",
                "background: transparent",
                "border: none",
            ),
        )

    def main_bg(self) -> str:
        """main bg용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"background-color: {self._c()['bg']};"

    def scroll_area_transparent(self) -> str:
        """scroll area transparent용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return "QScrollArea { border: none; background: transparent; }"

    def sidebar(self) -> str:
        """sidebar용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QWidget#sidebar",
            f"background-color: {c['sidebar_bg']}",
            f"border-right: 1px solid {c['border']}",
        )

    def sidebar_nav_title(self) -> str:
        """sidebar nav title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return (
            f"color: {c['muted']}; font-family: {FONT_FAMILY}; font-size: 9pt; font-weight: 600; "
            "text-transform: uppercase; letter-spacing: 0.08em; margin: 18px 10px 10px; "
            "background: transparent; border: none;"
        )

    def sidebar_card(self) -> str:
        """sidebar card용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QFrame",
            "margin-top: 18px",
            "padding: 14px",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._frame_radius_px}px",
            f"background-color: {c['card_bg']}",
        )

    def sidebar_card_title(self) -> str:
        """sidebar card title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"{FONT_TITLE} font-size: 11pt; margin: 0 0 8px; color: {c['text']}; background: transparent; border: none;"

    def sidebar_footer(self) -> str:
        """sidebar footer용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QFrame",
            "padding: 14px",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._frame_radius_px}px",
            f"background-color: {c['card_bg']}",
        )

    def sidebar_footer_value(self) -> str:
        """sidebar footer value용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"margin-top: 6px; font-family: {FONT_FAMILY}; font-size: 11pt; font-weight: 700; color: {c['text']}; background: transparent; border: none;"

    def topbar_title(self) -> str:
        """topbar title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"{FONT_LARGE_TITLE} margin: 0; color: {c['text']}; background: transparent; border: none;"

    def topbar_desc(self) -> str:
        """topbar desc용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"margin-top: 6px; {FONT_SUBTITLE} color: {c['muted']}; background: transparent; border: none;"

    def label_muted(self) -> str:
        """label muted용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"color: {c['muted']}; {FONT_BODY} font-size: 10pt; background: transparent; border: none;"

    def label_stat(self) -> str:
        """label stat용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"color: {c['muted']}; {FONT_STAT} margin: 0 0 8px 0; background: transparent; border: none;"

    def label_title(self) -> str:
        """label title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"{FONT_TITLE} font-size: 12pt; color: {c['text']}; background: transparent; border: none;"

    def line_edit(self) -> str:
        """line edit용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QLineEdit",
            f"background-color: {c['input_bg']}",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._input_radius_px}px",
            f"color: {c['text']}",
            "padding: 11px 12px",
        )

    def combo_box(self) -> str:
        """combo box용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_blocks(
            qss_block(
                "QComboBox",
                f"background-color: {c['input_bg']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._input_radius_px}px",
                f"color: {c['text']}",
                "padding: 11px 12px",
                "min-height: 20px",
            ),
            qss_block("QComboBox::drop-down", "border: none"),
        )

    def pill(self, color: str = "blue") -> str:
        """Pill 색상 키에 맞는 인라인 스타일 조각을 반환한다.

        Args:
            self: 이 인스턴스.
        color: blue|green|yellow|red.

        Returns:
            CSS 조각 문자열.
        """
        styles = {
            "blue": "background: rgba(122, 162, 255, 0.14); color: #bfd0ff; border: 1px solid rgba(122, 162, 255, 0.25);",
            "green": "background: rgba(74, 222, 128, 0.14); color: #b9f6ca; border: 1px solid rgba(74, 222, 128, 0.25);",
            "yellow": "background: rgba(255, 180, 84, 0.14); color: #ffd697; border: 1px solid rgba(255, 180, 84, 0.25);",
            "red": "background: rgba(255, 107, 129, 0.14); color: #ffc0cb; border: 1px solid rgba(255, 107, 129, 0.25);",
        }
        base = styles.get(color, styles["blue"])
        return f"padding: 6px 10px; border-radius: 999px; font-size: 9pt; {base}"

    def step_index_label(self) -> str:
        """step index label용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return "color: #ffffff; font-size: 9pt; font-weight: 700; background: transparent;"

    def badge_label(self, size: int) -> str:
        """배지 글자 크기에 맞는 라벨 스타일을 반환한다.

        Args:
            self: 이 인스턴스.
        size: 배지 한 변 픽셀.

        Returns:
            QSS 조각.
        """
        return f"color: #08101f; font-weight: 800; font-size: {max(10, int(round(max(14, size // 2) * 0.75)))}pt; background: transparent; border: none;"

    def nav_item(self) -> str:
        """nav item용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"""
        QPushButton {{
            width: 100%;
            text-align: left;
            padding: 12px 16px;
            border-radius: {self._button_radius_px}px;
            background: transparent;
            border: 1px solid transparent;
            color: {c["text"]};
            font-family: {FONT_FAMILY};
            font-size: 11pt;
            font-weight: 500;
        }}
        QPushButton:hover, QPushButton:checked {{
            background: rgba(122, 162, 255, 0.12);
            border-color: rgba(122, 162, 255, 0.28);
        }}
    """

    def step_row_title(self) -> str:
        """step row title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"color: {c['text']}; {FONT_TITLE} font-size: 10pt; background: transparent; border: none;"

    def step_row_text(self) -> str:
        """step row text용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"color: {c['text']}; {FONT_BODY} font-size: 10pt; background: transparent; border: none;"

    def brand_title(self) -> str:
        """brand title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_TITLE} font-size: 12pt; margin: 0; background: transparent; border: none;"

    def brand_subtitle(self) -> str:
        """brand subtitle용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_SUBTITLE} font-size: 10pt; margin-top: 4px; background: transparent; border: none;"

    def stat_card(self) -> str:
        """stat card용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_blocks(
            qss_block(
                "QFrame#stat_card",
                f"background-color: {c['card_bg']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._radius_px}px",
            ),
            qss_block("QFrame#stat_card QLabel", "background: transparent", "border: none"),
        )

    def stat_card_value(self) -> str:
        """stat card value용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"font-family: {FONT_FAMILY}; font-size: 20pt; font-weight: 800; color: {c['text']}; background: transparent; border: none; margin: 0;"

    def panel_header_title(self) -> str:
        """panel header title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_TITLE} font-size: 13pt; margin: 0; background: transparent; border: none;"

    def panel_header_desc(self) -> str:
        """panel header desc용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_SUBTITLE} margin-top: 6px; background: transparent; border: none;"

    def path_box(self) -> str:
        """path box용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QLabel",
            f"background-color: {c['input_bg']}",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._input_radius_px}px",
            "padding: 10px",
            'font-family: ui-monospace, "Cascadia Code", Consolas, monospace',
            f"color: {c['text']}",
            "font-size: 10pt",
        )

    def poster_card(self) -> str:
        """poster card용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QFrame",
            f"background-color: {c['panel2']}",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._frame_radius_px}px",
        )

    def frame_radius_px(self) -> int:
        """포스터 이미지·텍스트 패널 등에 쓰는 모서리 반경(px)을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            반경 픽셀.
        """
        return self._frame_radius_px

    def poster_card_image(self) -> str:
        """poster card image용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        r = self._frame_radius_px
        return (
            f"background-color: {c['input_bg']}; color: {c['muted']}; "
            f"border: none; border-radius: {r}px;"
        )

    def poster_card_title(self) -> str:
        """poster card title용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_TITLE} font-size: 12pt; margin: 0; background: transparent; border: none;"

    def poster_card_meta(self) -> str:
        """poster card meta용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_BODY} font-size: 10pt; line-height: 1.45; background: transparent; border: none;"

    def content_view_text_panel_overlay(self) -> str:
        """콘텐츠 뷰 이미지 하단 반투명 텍스트 패널 QSS를 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 문자열.
        """
        r = self._frame_radius_px
        return qss_block(
            "QFrame#content_view_text_panel",
            f"background-color: {self.CONTENT_VIEW_TEXT_PANEL_OVERLAY_BG}",
            "border: none",
            f"border-radius: {r}px",
        )

    def card_panel(self) -> str:
        """card panel용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QFrame",
            f"background-color: {c['card_bg']}",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._radius_px}px",
        )

    def list_item(self) -> str:
        """list item용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_block(
            "QWidget",
            f"background-color: {c['panel2']}",
            f"border: 1px solid {c['border']}",
            f"border-radius: {self._button_radius_px}px",
        )

    def list_item_strong(self) -> str:
        """list item strong용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"{FONT_TITLE} font-size: 11pt; margin-bottom: 6px; color: {c['text']}; background: transparent; border: none;"

    def list_item_muted(self) -> str:
        """list item muted용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        return f"{FONT_BODY} color: {self._c()['muted']}; background: transparent; border: none;"

    def form_label_muted(self) -> str:
        """form label muted용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return f"{FONT_CAPTION} color: {c['muted']}; background: transparent; border: none;"

    def view_toggle_button(self) -> str:
        """view toggle button용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
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
            font-size: 10pt;
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
        """view toggle menu용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_blocks(
            qss_block(
                "QMenu",
                f"background-color: {c['panel']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._menu_outer_radius_px}px",
                "padding: 6px",
            ),
            qss_block(
                "QMenu::item",
                "padding: 10px 24px",
                f"border-radius: {self._menu_item_radius_px}px",
                f"color: {c['text']}",
            ),
            qss_block("QMenu::item:selected", "background-color: rgba(122, 162, 255, 0.18)"),
            qss_block("QMenu::item:disabled", f"color: {c['muted']}"),
            qss_block(
                "QMenu::separator",
                "height: 1px",
                f"background: {c['border']}",
                "margin: 6px 8px",
            ),
        )

    def progress_dialog(self) -> str:
        """progress dialog용 QSS 또는 스타일 문자열을 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 또는 스타일 문자열.
        """
        c = self._c()
        return qss_blocks(
            qss_block(
                "QProgressDialog",
                f"background-color: {c['panel']}",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._radius_px}px",
                f"color: {c['text']}",
            ),
            qss_block(
                "QProgressDialog QLabel",
                f"color: {c['text']}",
                "font-size: 11pt",
            ),
            qss_block(
                "QProgressBar",
                f"border: 1px solid {c['border']}",
                f"border-radius: {self._progressbar_radius_px}px",
                "text-align: center",
                f"background-color: {c['input_bg']}",
            ),
            qss_block(
                "QProgressBar::chunk",
                f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent']}, stop:1 #8e8cff)",
                f"border-radius: {self._progressbar_chunk_radius_px}px",
            ),
        )
