"""User-facing GUI copy constants."""

from __future__ import annotations

from typing import Final

APP_WINDOW_TITLE: Final[str] = "AniVault V2"

SIDEBAR_TITLE: Final[str] = "Main Views"
SIDEBAR_TAB_LABELS: Final[dict[str, str]] = {
    "organizer": "Organizer",
    "subtitles": "\uc790\ub9c9\ub9cc",
    "settings": "Settings",
}

PAGE_META: Final[dict[str, tuple[str, str]]] = {
    "organizer": (
        "Organizer",
        "Handle scan, title grouping, TMDB matching, and final path preview in one place.",
    ),
    "subtitles": (
        "\uc790\ub9c9\ub9cc",
        "\ube44\ub514\uc624\uac00 \ub204\ub77d\ub418\uc5b4 \uc790\ub9c9 \ud30c\uc77c\ub9cc \ub530\ub85c \ud2b9\uc218 \uacbd\uc6b0\ub97c \uc2a4\uce94\u00b7\ub9e4\uce6d\ud558\uc5ec \uc774\ub3d9",
    ),
    "settings": (
        "Settings",
        "Configure scan/build controls plus path, parse, and TMDB rules.",
    ),
}

TOPBAR_DEFAULT_TITLE: Final[str] = PAGE_META["organizer"][0]
TOPBAR_DEFAULT_DESCRIPTION: Final[str] = PAGE_META["organizer"][1]

VIEW_TOGGLE_LABEL: Final[str] = "View"
VIEW_TOGGLE_DETAILS_PANE_LABEL: Final[str] = "Details Pane"

VIEW_LABELS: Final[dict[str, str]] = {
    "details": "Details",
    "content": "Content",
    "icon_xl": "Extra Large Icons",
    "icon_l": "Large Icons",
    "icon_m": "Medium Icons",
    "icon_s": "Small Icons",
    "icon_group": "Icons",
}

PIPELINE_RESULT_TITLE: Final[str] = "Pipeline Result"
PIPELINE_RESULT_DESCRIPTION: Final[str] = (
    "Review results in table, content, or icon views and choose the layout you want."
)

MATCH_PROGRESS_PREPARING: Final[str] = "Preparing TMDB matching..."
PARSE_PROGRESS_CACHE_CHECK: Final[str] = "Checking parse cache..."
PARSE_PROGRESS_PARSING: Final[str] = "Parsing filenames..."
