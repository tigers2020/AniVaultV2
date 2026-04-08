"""GUI component-level copy and tuning constants."""

from __future__ import annotations

from typing import Final

EXECUTION_CARD_STATUS_READY: Final[str] = "Ready"
EXECUTION_CARD_HEADER_TITLE: Final[str] = "Execution"
EXECUTION_CARD_HEADER_DESCRIPTION: Final[str] = (
    "Finalize move execution and rollback recent operations in one place."
)
EXECUTION_CARD_SUMMARY_TITLE: Final[str] = "Move Summary"
EXECUTION_CARD_SUMMARY_TEXT: Final[str] = (
    "8,975 files will be moved using resolution, year, Korean title group, and season folder rules."
)
EXECUTION_CARD_PILL_PREVIEW_COMPLETE: Final[str] = "Preview Complete"
EXECUTION_CARD_PILL_REVIEW_FILES: Final[str] = "73 Review Files"
EXECUTION_CARD_BUTTON_MOVE_FILES: Final[str] = "Move Files"
EXECUTION_CARD_BUTTON_CREATE_TREE: Final[str] = "Create Folder Tree Only"
EXECUTION_CARD_BUTTON_UNDO: Final[str] = "Undo Last Move"

FOLDER_SCAN_BAR_PATH_PLACEHOLDER: Final[str] = "스캔할 폴더 경로 (또는 폴더 선택 버튼)"
FOLDER_SCAN_BAR_BUTTON_SCAN: Final[str] = "스캔"
FOLDER_SCAN_BAR_BUTTON_MATCH: Final[str] = "TMDB 매칭"
FOLDER_SCAN_BAR_BUTTON_DRY_RUN: Final[str] = "Dry Run"

SCAN_BUILD_CARD_HEADER_TITLE: Final[str] = "Scan and Build Plan"
SCAN_BUILD_CARD_HEADER_DESCRIPTION: Final[str] = (
    "입력 폴더 스캔과 파이프라인 단계별 실행. 출력 루트(Target root)는 아래 Path Rules에서 설정"
)
SCAN_BUILD_CARD_HEADER_PILL_TEXT: Final[str] = "Pipeline Controls"
SCAN_BUILD_CARD_SOURCE_PLACEHOLDER: Final[str] = "Source: G:/Animations; D:/Incoming_Downloads"
SCAN_BUILD_CARD_TMDB_MODES: Final[list[str]] = [
    "TMDB TV Search",
    "TMDB Multi Search",
]
SCAN_BUILD_CARD_UNKNOWN_MODES: Final[list[str]] = [
    "Unknown to Needs_Review",
    "Leave unknown in source",
]
SCAN_BUILD_CARD_BUTTON_SCAN: Final[str] = "1. Scan Folder"
SCAN_BUILD_CARD_BUTTON_PARSE: Final[str] = "2. Parse Names"
SCAN_BUILD_CARD_BUTTON_QUERY_TMDB: Final[str] = "3. Query TMDB"
SCAN_BUILD_CARD_BUTTON_BUILD_PLAN: Final[str] = "4. Build Move Plan"

SETTINGS_ACTION_BAR_BUTTON_SAVE: Final[str] = "Save"
SETTINGS_ACTION_BAR_BUTTON_RESET: Final[str] = "Reset"
SETTINGS_ACTION_BAR_BUTTON_LOAD: Final[str] = "Load"

SCAN_PARSE_COORDINATOR_RESULT_GROUP_CHUNK_SIZE: Final[int] = 96
SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS: Final[int] = 1000
