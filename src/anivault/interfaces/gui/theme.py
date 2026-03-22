"""theme.py

테마 파사드: themes 패키지에 위임한다. QSS 생성 외 밀도 프로필 기반 레이아웃 픽셀 헬퍼를 제공한다.

Author: Pom Kim
"""

from typing import Any

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
    # responsive metrics
    "sidebar_width_px",
    "poster_min_card_width_px",
    "poster_grid_spacing_px",
    "layout_spacing_md",
    "layout_spacing_lg",
    "layout_main_padding",
]


def _t() -> Any:
    """현재 활성 테마 인스턴스를 반환한다.

    Args:
        없음.

    Returns:
        get_current_theme() 결과.
    """
    return get_current_theme()


def __getattr__(name: str) -> Any:
    """모듈 속성 지연 해석(COLORS 등).

    Args:
        name: 속성 이름.

    Returns:
        name이 COLORS이면 현재 테마의 colors.

    Raises:
        AttributeError: 지원하지 않는 속성 이름.
    """
    if name == "COLORS":
        return _t().colors
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def global_stylesheet() -> str:
    """앱 전역 QSS 문자열을 반환한다.

    Args:
        없음.

    Returns:
        global_stylesheet 문자열.
    """
    return str(_t().global_stylesheet())


def main_bg() -> str:
    """메인 배경 스타일 조각을 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().main_bg()


def scroll_area_transparent() -> str:
    """투명 스크롤 영역 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().scroll_area_transparent()


def sidebar() -> str:
    """사이드바 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar()


def sidebar_nav_title() -> str:
    """사이드바 내비 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar_nav_title()


def sidebar_card() -> str:
    """사이드바 카드 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar_card()


def sidebar_card_title() -> str:
    """사이드바 카드 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar_card_title()


def sidebar_footer() -> str:
    """사이드바 푸터 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar_footer()


def sidebar_footer_value() -> str:
    """사이드바 푸터 값 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().sidebar_footer_value()


def topbar_title() -> str:
    """탑바 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().topbar_title()


def topbar_desc() -> str:
    """탑바 설명 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().topbar_desc()


def label_muted() -> str:
    """muted 라벨 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().label_muted()


def label_stat() -> str:
    """통계 라벨 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().label_stat()


def label_title() -> str:
    """제목 라벨 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().label_title()


def line_edit() -> str:
    """LineEdit QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().line_edit()


def combo_box() -> str:
    """ComboBox QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().combo_box()


def pill(color: str = "blue") -> str:
    """Pill 색상별 QSS를 반환한다.

    Args:
        color: 색상 키(예: blue).

    Returns:
        QSS 문자열.
    """
    return _t().pill(color)


def step_index_label() -> str:
    """단계 인덱스 라벨 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().step_index_label()


def badge_label(size: int) -> str:
    """배지 라벨 QSS를 반환한다.

    Args:
        size: 배지 한 변 픽셀.

    Returns:
        QSS 문자열.
    """
    return _t().badge_label(size)


def nav_item() -> str:
    """내비 항목 버튼 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().nav_item()


def step_row_title() -> str:
    """스텝 행 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().step_row_title()


def step_row_text() -> str:
    """스텝 행 본문 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().step_row_text()


def brand_title() -> str:
    """브랜드 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().brand_title()


def brand_subtitle() -> str:
    """브랜드 부제 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().brand_subtitle()


def stat_card() -> str:
    """통계 카드 프레임 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().stat_card()


def stat_card_value() -> str:
    """통계 카드 값 라벨 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().stat_card_value()


def panel_header_title() -> str:
    """패널 헤더 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().panel_header_title()


def panel_header_desc() -> str:
    """패널 헤더 설명 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().panel_header_desc()


def path_box() -> str:
    """경로 박스 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().path_box()


def poster_card() -> str:
    """포스터 카드 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().poster_card()


def frame_radius_px() -> int:
    """카드·입력 프레임 모서리 반경(px)을 반환한다.

    Args:
        없음.

    Returns:
        반경 픽셀.
    """
    return _t().frame_radius_px()


def poster_card_image() -> str:
    """포스터 카드 이미지 영역 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().poster_card_image()


def poster_card_title() -> str:
    """포스터 카드 제목 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().poster_card_title()


def poster_card_meta() -> str:
    """포스터 카드 메타 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().poster_card_meta()


def content_view_text_panel_overlay() -> str:
    """콘텐츠 뷰 텍스트 패널 오버레이 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().content_view_text_panel_overlay()


def card_panel() -> str:
    """카드 패널 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().card_panel()


def list_item() -> str:
    """리스트 항목 컨테이너 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().list_item()


def list_item_strong() -> str:
    """리스트 항목 강조 줄 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().list_item_strong()


def list_item_muted() -> str:
    """리스트 항목 보조 줄 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().list_item_muted()


def form_label_muted() -> str:
    """폼 라벨 muted QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().form_label_muted()


def view_toggle_button() -> str:
    """뷰 토글 버튼 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().view_toggle_button()


def view_toggle_menu() -> str:
    """뷰 토글 메뉴 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().view_toggle_menu()


def progress_dialog() -> str:
    """진행 대화상자 QSS를 반환한다.

    Args:
        없음.

    Returns:
        QSS 문자열.
    """
    return _t().progress_dialog()


# ---- Responsive layout metrics ----
# Base metrics are aligned with the previous hard-coded px constants.
_POSTER_MIN_CARD_WIDTH_BASE_PX = 150
_POSTER_GRID_SPACING_BASE_PX = 13


def _p() -> DensityProfile:
    """현재 밀도 프로필을 반환한다.

    Args:
        없음.

    Returns:
        DensityProfile.
    """
    return get_profile(get_current_density_key())


def sidebar_width_px() -> int:
    """반응형 사이드바 너비(px)를 반환한다.

    Args:
        없음.

    Returns:
        스케일된 너비.
    """
    p = _p()
    return scaled_int(
        SIDEBAR_WIDTH_PX,
        p.sidebar_width_scale,
        minimum=240,
        maximum=380,
    )


def poster_min_card_width_px() -> int:
    """포스터 카드 최소 너비(px)를 반환한다.

    Args:
        없음.

    Returns:
        스케일된 최소 너비.
    """
    p = _p()
    return scaled_int(
        _POSTER_MIN_CARD_WIDTH_BASE_PX,
        p.card_min_width_scale,
        minimum=110,
        maximum=280,
    )


def poster_grid_spacing_px() -> int:
    """포스터 그리드 간격(px)을 반환한다.

    Args:
        없음.

    Returns:
        스케일된 간격.
    """
    p = _p()
    return scaled_int(
        _POSTER_GRID_SPACING_BASE_PX,
        p.grid_spacing_scale,
        minimum=7,
        maximum=22,
    )


def layout_spacing_md() -> int:
    """페이지 본문 세로 간격(기준 16px).

    Args:
        없음.

    Returns:
        스케일된 픽셀.
    """
    p = _p()
    return scaled_int(16, p.grid_spacing_scale, minimum=10, maximum=24)


def layout_spacing_lg() -> int:
    """가로 두 열·카드 행 간 간격(기준 18px).

    Args:
        없음.

    Returns:
        스케일된 픽셀.
    """
    p = _p()
    return scaled_int(18, p.grid_spacing_scale, minimum=12, maximum=26)


def layout_main_padding() -> int:
    """메인 셸 콘텐츠 영역 패딩(기준 26px).

    Args:
        없음.

    Returns:
        스케일된 픽셀.
    """
    p = _p()
    return scaled_int(26, p.scale, minimum=18, maximum=36)
