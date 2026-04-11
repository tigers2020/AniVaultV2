"""User-facing GUI copy constants."""

from __future__ import annotations

from typing import Final

APP_WINDOW_TITLE: Final[str] = "AniVault V2"

SIDEBAR_TITLE: Final[str] = "화면"
SIDEBAR_TAB_LABELS: Final[dict[str, str]] = {
    "organizer": "정리 작업",
    "subtitles": "자막만",
    "settings": "설정",
}

PAGE_META: Final[dict[str, tuple[str, str]]] = {
    "organizer": (
        "정리 작업",
        "폴더를 스캔하고, TMDB에서 제목을 찾은 뒤, 파일이 이동될 위치를 미리 확인하세요.",
    ),
    "subtitles": (
        "자막만",
        "비디오 없이 자막 파일만 있는 폴더를 따로 스캔하고 정리합니다.",
    ),
    "settings": (
        "설정",
        "스캔, 저장 위치, 파일명 읽기, TMDB 옵션을 조정합니다.",
    ),
}

TOPBAR_DEFAULT_TITLE: Final[str] = PAGE_META["organizer"][0]
TOPBAR_DEFAULT_DESCRIPTION: Final[str] = PAGE_META["organizer"][1]

VIEW_TOGGLE_LABEL: Final[str] = "보기"
VIEW_TOGGLE_DETAILS_PANE_LABEL: Final[str] = "상세 패널"

VIEW_LABELS: Final[dict[str, str]] = {
    "details": "상세",
    "content": "내용",
    "icon_xl": "아주 큰 아이콘",
    "icon_l": "큰 아이콘",
    "icon_m": "중간 아이콘",
    "icon_s": "작은 아이콘",
    "icon_group": "아이콘",
}

PIPELINE_RESULT_TITLE: Final[str] = "작업 결과"
PIPELINE_RESULT_DESCRIPTION: Final[str] = (
    "테이블, 내용, 아이콘 보기로 파일을 확인하세요. 보기에서 레이아웃을 바꿀 수 있습니다."
)

MATCH_PROGRESS_PREPARING: Final[str] = "TMDB 매칭 준비 중…"
PARSE_PROGRESS_CACHE_CHECK: Final[str] = "캐시 확인 중…"
PARSE_PROGRESS_PARSING: Final[str] = "파일명에서 제목 읽는 중…"
