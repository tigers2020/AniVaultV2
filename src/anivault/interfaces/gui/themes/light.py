"""light.py

주간용 밝은 팔레트 라이트 테마.

Author: Pom Kim
"""

from anivault.interfaces.gui.themes.base import ColorPalette
from anivault.interfaces.gui.themes.dark import DarkTheme


class LightTheme(DarkTheme):
    """DarkTheme QSS 구조를 유지하고 팔레트만 밝게 바꾼다."""

    def __init__(self, *, scale: float = 1.0) -> None:
        """라이트 ColorPalette를 설정하고 colors를 갱신한다.

        Args:
            self: 이 인스턴스.
            scale: 반응형 타이포·메트릭 배율.

        Returns:
            None.
        """
        super().__init__(scale=scale)
        self.palette = ColorPalette(
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
        self.colors = self.palette.to_dict()

    def content_view_text_panel_overlay(self) -> str:
        """밝은 배경용 약한 오버레이 QSS를 반환한다.

        Args:
            self: 이 인스턴스.

        Returns:
            QSS 문자열.
        """
        r = self._frame_radius_px
        return f"""
        QFrame#content_view_text_panel {{
            background-color: rgba(0, 0, 0, 0.22);
            border: none;
            border-radius: {r}px;
        }}
        """
