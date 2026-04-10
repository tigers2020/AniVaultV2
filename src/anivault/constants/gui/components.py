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

PIPELINE_BUSY_TITLE: Final[str] = "작업 진행 중"
PIPELINE_BUSY_MESSAGE: Final[str] = (
    "스캔, TMDB 매칭, Dry Run 등 다른 작업이 끝날 때까지 기다려 주세요."
)

SCAN_BUILD_CARD_HEADER_TITLE: Final[str] = "Scan and Build Plan"
SCAN_BUILD_CARD_HEADER_DESCRIPTION: Final[str] = (
    "입력 폴더 스캔과 파이프라인 단계별 실행. 출력 루트(Target root)는 아래 Path Rules에서 설정"
)
SCAN_BUILD_CARD_HEADER_PILL_TEXT: Final[str] = "Pipeline Controls"
SCAN_BUILD_CARD_SOURCE_PLACEHOLDER: Final[str] = "Source: G:/Animations; D:/Incoming_Downloads"

SETTINGS_ACTION_BAR_BUTTON_SAVE: Final[str] = "Save"
SETTINGS_ACTION_BAR_BUTTON_RESET: Final[str] = "Reset"
SETTINGS_ACTION_BAR_BUTTON_LOAD: Final[str] = "Load"

PARSE_TMDB_FORM_HEADER_TITLE: Final[str] = "Parse and TMDB Rules"
PARSE_TMDB_FORM_HEADER_DESCRIPTION: Final[str] = "파일명 파싱과 TMDB 한글 제목 매핑 기준"
PARSE_TMDB_FORM_LABEL_API_KEY: Final[str] = "TMDB API key"
PARSE_TMDB_FORM_API_KEY_HELP: Final[str] = "Stored in .env as TMDB_API_KEY"
PARSE_TMDB_FORM_LABEL_IGNORE_TOKENS: Final[str] = "Ignore tokens"
PARSE_TMDB_FORM_LABEL_SEASON_FORMAT: Final[str] = "Season folder format"

PATH_RULES_FORM_HEADER_TITLE: Final[str] = "Path Rules"
PATH_RULES_FORM_HEADER_DESCRIPTION: Final[str] = "최종 출력 구조와 기본값 설정"
PATH_RULES_FORM_LABEL_TARGET_ROOT: Final[str] = "Target root folder"
PATH_RULES_FORM_LABEL_TEMPLATE: Final[str] = "Path template"
PATH_RULES_FORM_LABEL_UNKNOWN_RESOLUTION: Final[str] = "Unknown resolution"
PATH_RULES_FORM_LABEL_UNKNOWN_GROUP: Final[str] = "Unknown group folder"

TMDB_MANUAL_DIALOG_TITLE: Final[str] = "TMDB 수동 매칭"
TMDB_MANUAL_DIALOG_LABEL_QUERY: Final[str] = "검색어"
TMDB_MANUAL_DIALOG_QUERY_PLACEHOLDER: Final[str] = "검색어 (예: 입력한 작품 제목)"
TMDB_MANUAL_DIALOG_LABEL_YEAR: Final[str] = "연도(선택)"
TMDB_MANUAL_DIALOG_YEAR_PLACEHOLDER: Final[str] = "비우면 연도 무시 (예: 2024)"
TMDB_MANUAL_DIALOG_RESULTS_TITLE: Final[str] = "검색 결과"
TMDB_MANUAL_DIALOG_BUTTON_SEARCH: Final[str] = "검색"
TMDB_MANUAL_DIALOG_BUTTON_OK: Final[str] = "확인"
TMDB_MANUAL_DIALOG_BUTTON_CANCEL: Final[str] = "취소"
TMDB_MANUAL_DIALOG_EMPTY_SELECTION_TITLE: Final[str] = "선택 없음"
TMDB_MANUAL_DIALOG_EMPTY_SELECTION_MESSAGE: Final[str] = (
    "목록에서 한 항목을 선택하거나 검색 결과가 있어야 합니다."
)
TMDB_MANUAL_DIALOG_UNKNOWN_TITLE: Final[str] = "제목 없음"
TMDB_MANUAL_DIALOG_UNKNOWN_YEAR: Final[str] = "연도 미상"
TMDB_MANUAL_DIALOG_RESULT_ITEM_TEMPLATE: Final[str] = "{line}\nID {tmdb_id} · {year}"

DRY_RUN_DIALOG_TITLE: Final[str] = "Dry Run 및 이동 미리보기"
DRY_RUN_DIALOG_HEADER_SOURCE: Final[str] = "원본 경로"
DRY_RUN_DIALOG_HEADER_DESTINATION: Final[str] = "대상 경로"
DRY_RUN_DIALOG_BUTTON_APPLY: Final[str] = "실제 이동"
DRY_RUN_DIALOG_BUTTON_CLOSE: Final[str] = "닫기"

SCAN_PARSE_COORDINATOR_RESULT_GROUP_CHUNK_SIZE: Final[int] = 96
DRY_RUN_DIALOG_HEADER_GROUP: Final[str] = "Group"
DRY_RUN_DIALOG_HEADER_RESOLUTION: Final[str] = "Resolution"
SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS: Final[int] = 1000
SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_TITLE: Final[str] = "스캔 경로 오류"
SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_MESSAGE_TEMPLATE: Final[str] = (
    "지정한 폴더를 읽을 수 없습니다(스토리지, 권한, 이동식 드라이브 등).\n\n{path}\n\n{error}"
)
SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_TITLE: Final[str] = "스캔 경로 없음"
SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_MESSAGE_TEMPLATE: Final[str] = (
    "폴더가 없거나 읽을 수 없습니다. 경로를 확인하거나 다시 선택하세요.\n\n{path}"
)
SCAN_PARSE_COORDINATOR_SCAN_PATH_EMPTY_MESSAGE: Final[str] = "스캔할 폴더를 먼저 선택해 주세요."
SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_TITLE: Final[str] = "스캔 중"
SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_MESSAGE: Final[str] = "폴더 스캔 중..."
SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_TITLE: Final[str] = "Parse 중"
SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_MESSAGE: Final[str] = "파일명 파싱 중..."
SCAN_PARSE_COORDINATOR_STATUS_SCANNED: Final[str] = "스캔됨"
SCAN_PARSE_COORDINATOR_STATUS_PARSED: Final[str] = "파싱됨"
PIPELINE_ROW_STATUS_TMDB_CACHED: Final[str] = "TMDB 캐시 로드"
PIPELINE_ROW_STATUS_MOVED: Final[str] = "이동됨"
MANUAL_TMDB_RELAY_ERROR_TITLE: Final[str] = "TMDB 검색 실패"

PATH_SELECT_FIELD_PLACEHOLDER: Final[str] = "폴더 경로"
PATH_SELECT_FIELD_BROWSE_BUTTON: Final[str] = "폴더 선택"
PATH_SELECT_FIELD_DIALOG_TITLE: Final[str] = "폴더 선택"

DETAILS_PANE_EMPTY_STATE: Final[str] = "항목을 선택하세요"
DETAILS_PANE_MANUAL_MATCH_BUTTON: Final[str] = "TMDB 수동 매칭"
DETAILS_PANE_GROUP_FILES_LABEL: Final[str] = "파일"
DETAILS_PANE_ORIGINAL_FILE_LABEL: Final[str] = "원본 파일"
DETAILS_PANE_PARSED_TITLE_LABEL: Final[str] = "Parsed Title"
DETAILS_PANE_PARSE_GROUP_LABEL: Final[str] = "Parse Group"
DETAILS_PANE_TMDB_TITLE_LABEL: Final[str] = "TMDB 한글"
DETAILS_PANE_YEAR_SEASON_EP_LABEL: Final[str] = "Year / Season / Ep"
DETAILS_PANE_RESOLUTION_LABEL: Final[str] = "해상도"
DETAILS_PANE_STATUS_LABEL: Final[str] = "상태"
DETAILS_PANE_TARGET_PATH_LABEL: Final[str] = "대상 경로"
DETAILS_PANE_MEMBER_META_JOINER: Final[str] = " · "

PIPELINE_RESULT_PANEL_HEADER_TITLE: Final[str] = "Pipeline Result"
PIPELINE_RESULT_PANEL_HEADER_DESCRIPTION: Final[str] = (
    "테이블·내용·아이콘 그리드로 결과를 볼 수 있습니다. 보기에서 레이아웃을 선택하세요."
)
PIPELINE_RESULT_PANEL_MATCHED_LABEL: Final[str] = "TMDB 한글 제목 있음"
PIPELINE_ROW_STATUS_TMDB_MATCHED: Final[str] = "TMDB 매칭됨"
PIPELINE_RESULT_PANEL_UNMATCHED_LABEL: Final[str] = "미매칭·미진행"

PROGRESS_DIALOG_DEFAULT_TITLE: Final[str] = "진행 중"
PROGRESS_DIALOG_DEFAULT_MESSAGE: Final[str] = "처리 중입니다..."

CONTENT_VIEW_MULTI_FILE_SUFFIX: Final[str] = "개 파일"
CONTENT_VIEW_META_JOINER: Final[str] = " · "
CONTENT_VIEW_GROUP_FILES_LABEL: Final[str] = "파일"
CONTENT_VIEW_ORIGINAL_FILE_LABEL: Final[str] = "원본 파일"
CONTENT_VIEW_PARSED_LABEL: Final[str] = "Parsed"
CONTENT_VIEW_TMDB_LABEL: Final[str] = "TMDB"
CONTENT_VIEW_YEAR_SEASON_LABEL: Final[str] = "연도/시즌"
CONTENT_VIEW_RESOLUTION_LABEL: Final[str] = "해상도"
CONTENT_VIEW_PATH_LABEL: Final[str] = "경로"

MATCH_COORDINATOR_MISSING_API_TITLE: Final[str] = "TMDB API 키 없음"
MATCH_COORDINATOR_MISSING_API_MESSAGE: Final[str] = (
    "Settings → Parse/TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요."
)
MATCH_COORDINATOR_NO_ROWS_TITLE: Final[str] = "매칭할 항목 없음"
MATCH_COORDINATOR_NO_ROWS_MESSAGE: Final[str] = (
    "먼저 폴더를 스캔하고 파싱이 끝난 뒤 다시 시도하세요."
)
MATCH_COORDINATOR_PROGRESS_TITLE: Final[str] = "TMDB 매칭"
MATCH_COORDINATOR_PROGRESS_MESSAGE: Final[str] = "한글 제목 조회 중..."
MATCH_COORDINATOR_NO_SELECTION_TITLE: Final[str] = "선택 없음"
MATCH_COORDINATOR_NO_SELECTION_MESSAGE: Final[str] = "파이프라인에서 항목을 먼저 선택하세요."
MATCH_COORDINATOR_EMPTY_QUERY_TITLE: Final[str] = "검색어 없음"
MATCH_COORDINATOR_EMPTY_QUERY_MESSAGE: Final[str] = "검색어를 입력하세요."

PLAN_APPLY_EMPTY_TITLE: Final[str] = "항목 없음"
PLAN_APPLY_EMPTY_MESSAGE: Final[str] = "먼저 스캔·매칭을 완료하세요."
PLAN_APPLY_NO_MATCHED_TITLE: Final[str] = "TMDB 매칭 없음"
PLAN_APPLY_NO_MATCHED_MESSAGE: Final[str] = (
    "TMDB 한글 제목이 있는 항목이 없습니다. 자동·수동 매칭으로 준비한 뒤 다시 시도하세요."
)
PLAN_APPLY_PATH_RULES_TITLE: Final[str] = "경로 규칙"
PLAN_APPLY_PATH_RULES_MESSAGE: Final[str] = (
    "Settings → Path Rules에서 Target root와 Path template을 설정하세요."
)
PLAN_APPLY_PLAN_PROGRESS_TITLE: Final[str] = "플랜 생성"
PLAN_APPLY_PLAN_PROGRESS_MESSAGE: Final[str] = "경로 계획 중..."
PLAN_APPLY_PLAN_ERROR_TITLE: Final[str] = "플랜 오류"
PLAN_APPLY_DRY_RUN_TITLE: Final[str] = "Dry Run"
PLAN_APPLY_DRY_RUN_EMPTY_MESSAGE: Final[str] = "이동할 항목이 없습니다."
PLAN_APPLY_EXECUTE_UNAVAILABLE_TITLE: Final[str] = "실제 이동 불가"
PLAN_APPLY_EXECUTE_UNAVAILABLE_MESSAGE: Final[str] = (
    "실제 이동 기능이 연결되지 않았습니다. 앱을 다시 실행해 주세요."
)
PLAN_APPLY_LOG_ROOT_TITLE: Final[str] = "로그 경로"
PLAN_APPLY_LOG_ROOT_MESSAGE: Final[str] = "스캔 소스 경로 또는 Target root를 설정해야 합니다."
PLAN_APPLY_MOVE_PROGRESS_TITLE: Final[str] = "파일 이동"
PLAN_APPLY_MOVE_PROGRESS_MESSAGE: Final[str] = "이동 중..."
PLAN_APPLY_MOVE_ERROR_TITLE: Final[str] = "이동 오류"
PLAN_APPLY_COMPLETE_TITLE: Final[str] = "완료"
PLAN_APPLY_COMPLETE_MESSAGE_TEMPLATE: Final[str] = "{moved_count}개 파일을 이동했습니다."
