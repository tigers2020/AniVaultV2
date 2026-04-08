"""base.py

테마 기반: ColorPalette와 QSS 생성용 상수.

Author: Pom Kim
"""

from dataclasses import dataclass

from anivault.constants.gui.theme import (
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

__all__ = [
    "ColorPalette",
    "FONT_FAMILY",
    "FONT_TITLE",
    "FONT_SUBTITLE",
    "FONT_BODY",
    "FONT_CAPTION",
    "FONT_LARGE_TITLE",
    "FONT_STAT",
    "RADIUS_PX",
    "SIDEBAR_WIDTH_PX",
]


@dataclass
class ColorPalette:
    """앱 UI 색상 팔레트."""

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
        """팔레트 필드를 문자열 dict로 반환한다.

        Args:
            self: 이 팔레트.

        Returns:
            키→색상 문자열.
        """
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
