"""GUI component-level copy and tuning constants."""

from __future__ import annotations

from typing import Final

EXECUTION_CARD_STATUS_READY: Final[str] = "Ready"
EXECUTION_CARD_HEADER_TITLE: Final[str] = "Move files"
EXECUTION_CARD_HEADER_DESCRIPTION: Final[str] = (
    "Run the file move or undo a recent move."
)
EXECUTION_CARD_SUMMARY_TITLE: Final[str] = "Move summary"
EXECUTION_CARD_SUMMARY_TEXT: Final[str] = (
    "8,975 files will be moved using resolution, year, Korean title, and season folder rules."
)
EXECUTION_CARD_PILL_PREVIEW_COMPLETE: Final[str] = "Preview complete"
EXECUTION_CARD_PILL_REVIEW_FILES: Final[str] = "73 review files"
EXECUTION_CARD_BUTTON_MOVE_FILES: Final[str] = "Move files"
EXECUTION_CARD_BUTTON_CREATE_TREE: Final[str] = "Create folder tree only"
EXECUTION_CARD_BUTTON_UNDO: Final[str] = "Undo last move"

FOLDER_SCAN_BAR_PATH_PLACEHOLDER: Final[str] = "스캔할 폴더 경로 (또는 폴더 선택 버튼)"
FOLDER_SCAN_BAR_BUTTON_SCAN: Final[str] = "스캔"
FOLDER_SCAN_BAR_BUTTON_MATCH: Final[str] = "제목 매칭"
FOLDER_SCAN_BAR_BUTTON_DRY_RUN: Final[str] = "미리보기"

PIPELINE_BUSY_TITLE: Final[str] = "작업 진행 중"
PIPELINE_BUSY_MESSAGE: Final[str] = (
    "스캔, TMDB 매칭, 미리보기 등 현재 작업이 끝날 때까지 기다려 주세요."
)

SCAN_BUILD_CARD_HEADER_TITLE: Final[str] = "폴더 스캔"
SCAN_BUILD_CARD_HEADER_DESCRIPTION: Final[str] = (
    "입력 폴더를 단계별로 스캔합니다. 정리할 위치는 아래 저장 위치 규칙에서 지정하세요."
)
SCAN_BUILD_CARD_HEADER_PILL_TEXT: Final[str] = "작업 단계"
SCAN_BUILD_CARD_SOURCE_PLACEHOLDER: Final[str] = "예: G:/Animations; D:/Incoming_Downloads"

SETTINGS_ACTION_BAR_BUTTON_SAVE: Final[str] = "Save"
SETTINGS_ACTION_BAR_BUTTON_RESET: Final[str] = "Reset"
SETTINGS_ACTION_BAR_BUTTON_LOAD: Final[str] = "Load"

PARSE_TMDB_FORM_HEADER_TITLE: Final[str] = "파일명 및 TMDB"
PARSE_TMDB_FORM_HEADER_DESCRIPTION: Final[str] = (
    "파일명에서 제목을 읽는 방식과 TMDB 한국어 제목 연결 기준"
)
PARSE_TMDB_FORM_LABEL_API_KEY: Final[str] = "TMDB API key"
PARSE_TMDB_FORM_API_KEY_HELP: Final[str] = "Stored in .env as TMDB_API_KEY"
PARSE_TMDB_FORM_LABEL_IGNORE_TOKENS: Final[str] = "무시할 단어"
PARSE_TMDB_FORM_LABEL_SEASON_FORMAT: Final[str] = "시즌 폴더 형식"

PATH_RULES_FORM_HEADER_TITLE: Final[str] = "저장 위치 규칙"
PATH_RULES_FORM_HEADER_DESCRIPTION: Final[str] = "정리된 파일이 저장될 위치와 폴더 이름 규칙"
PATH_RULES_FORM_LABEL_TARGET_ROOT: Final[str] = "정리할 위치"
PATH_RULES_FORM_LABEL_TEMPLATE: Final[str] = "폴더 이름 규칙"
PATH_RULES_FORM_LABEL_UNKNOWN_RESOLUTION: Final[str] = "해상도 미확인 시"
PATH_RULES_FORM_LABEL_UNKNOWN_GROUP: Final[str] = "그룹 미확인 시 폴더"

TMDB_MANUAL_DIALOG_TITLE: Final[str] = "TMDB에서 제목 찾기"
TMDB_MANUAL_DIALOG_LABEL_QUERY: Final[str] = "검색어"
TMDB_MANUAL_DIALOG_QUERY_PLACEHOLDER: Final[str] = "검색할 제목 (예: 작품 이름)"
TMDB_MANUAL_DIALOG_LABEL_YEAR: Final[str] = "연도(선택)"
TMDB_MANUAL_DIALOG_YEAR_PLACEHOLDER: Final[str] = "비우면 연도 무시 (예: 2024)"
TMDB_MANUAL_DIALOG_RESULTS_TITLE: Final[str] = "검색 결과"
TMDB_MANUAL_DIALOG_BUTTON_SEARCH: Final[str] = "검색"
TMDB_MANUAL_DIALOG_BUTTON_OK: Final[str] = "확인"
TMDB_MANUAL_DIALOG_BUTTON_CANCEL: Final[str] = "취소"
TMDB_MANUAL_DIALOG_EMPTY_SELECTION_TITLE: Final[str] = "선택 없음"
TMDB_MANUAL_DIALOG_EMPTY_SELECTION_MESSAGE: Final[str] = (
    "목록에서 항목을 선택하거나 먼저 검색하세요."
)
TMDB_MANUAL_DIALOG_UNKNOWN_TITLE: Final[str] = "제목 없음"
TMDB_MANUAL_DIALOG_UNKNOWN_YEAR: Final[str] = "연도 미상"
TMDB_MANUAL_DIALOG_RESULT_ITEM_TEMPLATE: Final[str] = "{line}\nID {tmdb_id} · {year}"

DRY_RUN_DIALOG_TITLE: Final[str] = "미리보기 및 이동"
DRY_RUN_DIALOG_HEADER_SOURCE: Final[str] = "현재 경로"
DRY_RUN_DIALOG_HEADER_DESTINATION: Final[str] = "이동할 경로"
DRY_RUN_DIALOG_BUTTON_APPLY: Final[str] = "이동 실행"
DRY_RUN_DIALOG_BUTTON_CLOSE: Final[str] = "닫기"

SCAN_PARSE_COORDINATOR_RESULT_GROUP_CHUNK_SIZE: Final[int] = 96
DRY_RUN_DIALOG_HEADER_GROUP: Final[str] = "그룹"
DRY_RUN_DIALOG_HEADER_RESOLUTION: Final[str] = "해상도"
SCAN_PARSE_COORDINATOR_MID_SCAN_MODEL_MAX_GROUPS: Final[int] = 1000
SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_TITLE: Final[str] = "폴더를 읽을 수 없음"
SCAN_PARSE_COORDINATOR_SCAN_PATH_ERROR_MESSAGE_TEMPLATE: Final[str] = (
    "지정한 폴더를 읽을 수 없습니다(저장소, 권한, 이동식 드라이브 등).\n\n{path}\n\n{error}"
)
SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_TITLE: Final[str] = "폴더를 찾을 수 없음"
SCAN_PARSE_COORDINATOR_SCAN_PATH_MISSING_MESSAGE_TEMPLATE: Final[str] = (
    "폴더가 없거나 읽을 수 없습니다. 경로를 확인하거나 다시 선택하세요.\n\n{path}"
)
SCAN_PARSE_COORDINATOR_SCAN_PATH_EMPTY_MESSAGE: Final[str] = (
    "스캔할 폴더를 먼저 선택해 주세요."
)
SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_TITLE: Final[str] = "스캔 중"
SCAN_PARSE_COORDINATOR_SCAN_PROGRESS_MESSAGE: Final[str] = "폴더 스캔 중…"
SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_TITLE: Final[str] = "제목 읽는 중"
SCAN_PARSE_COORDINATOR_PARSE_PROGRESS_MESSAGE: Final[str] = (
    "파일명에서 제목을 읽고 있습니다…"
)
# --- Status constants stored in PipelineRow.status (DO NOT CHANGE VALUES) ---
SCAN_PARSE_COORDINATOR_STATUS_SCANNED: Final[str] = "스캔됨"
SCAN_PARSE_COORDINATOR_STATUS_PARSED: Final[str] = "파싱됨"
PIPELINE_ROW_STATUS_TMDB_CACHED: Final[str] = "TMDB 캐시 로드"
PIPELINE_ROW_STATUS_MOVED: Final[str] = "이동됨"
MANUAL_TMDB_RELAY_ERROR_TITLE: Final[str] = "TMDB 검색 실패"

PATH_SELECT_FIELD_PLACEHOLDER: Final[str] = "폴더 경로"
PATH_SELECT_FIELD_BROWSE_BUTTON: Final[str] = "폴더 선택"
PATH_SELECT_FIELD_DIALOG_TITLE: Final[str] = "폴더 선택"

DETAILS_PANE_EMPTY_STATE: Final[str] = "항목을 선택하세요"
DETAILS_PANE_MANUAL_MATCH_BUTTON: Final[str] = "TMDB에서 제목 찾기"
DETAILS_PANE_GROUP_FILES_LABEL: Final[str] = "파일"
DETAILS_PANE_ORIGINAL_FILE_LABEL: Final[str] = "원본 파일"
DETAILS_PANE_PARSED_TITLE_LABEL: Final[str] = "파일명 제목"
DETAILS_PANE_PARSE_GROUP_LABEL: Final[str] = "제목 그룹"
DETAILS_PANE_TMDB_TITLE_LABEL: Final[str] = "TMDB 한국어 제목"
DETAILS_PANE_YEAR_SEASON_EP_LABEL: Final[str] = "연도 / 시즌 / 화"
DETAILS_PANE_RESOLUTION_LABEL: Final[str] = "해상도"
DETAILS_PANE_STATUS_LABEL: Final[str] = "상태"
DETAILS_PANE_TARGET_PATH_LABEL: Final[str] = "이동할 위치"
DETAILS_PANE_MEMBER_META_JOINER: Final[str] = " · "

PIPELINE_RESULT_PANEL_HEADER_TITLE: Final[str] = "작업 결과"
PIPELINE_RESULT_PANEL_HEADER_DESCRIPTION: Final[str] = (
    "테이블, 내용, 아이콘 보기로 파일을 확인하세요. 보기에서 레이아웃을 바꿀 수 있습니다."
)
PIPELINE_RESULT_PANEL_MATCHED_LABEL: Final[str] = "TMDB 한국어 제목 있음"
# --- Status constant stored in PipelineRow.status (DO NOT CHANGE VALUE) ---
PIPELINE_ROW_STATUS_TMDB_MATCHED: Final[str] = "TMDB 매칭됨"
PIPELINE_RESULT_PANEL_UNMATCHED_LABEL: Final[str] = "아직 매칭되지 않음"

PROGRESS_DIALOG_DEFAULT_TITLE: Final[str] = "진행 중"
PROGRESS_DIALOG_DEFAULT_MESSAGE: Final[str] = "처리 중입니다…"

CONTENT_VIEW_MULTI_FILE_SUFFIX: Final[str] = "개 파일"
CONTENT_VIEW_META_JOINER: Final[str] = " · "
CONTENT_VIEW_GROUP_FILES_LABEL: Final[str] = "파일"
CONTENT_VIEW_ORIGINAL_FILE_LABEL: Final[str] = "원본 파일"
CONTENT_VIEW_PARSED_LABEL: Final[str] = "파일명 제목"
CONTENT_VIEW_TMDB_LABEL: Final[str] = "TMDB"
CONTENT_VIEW_YEAR_SEASON_LABEL: Final[str] = "연도 / 시즌"
CONTENT_VIEW_RESOLUTION_LABEL: Final[str] = "해상도"
CONTENT_VIEW_PATH_LABEL: Final[str] = "경로"

MATCH_COORDINATOR_MISSING_API_TITLE: Final[str] = "TMDB API 키 없음"
MATCH_COORDINATOR_MISSING_API_MESSAGE: Final[str] = (
    "설정 → 파일명 및 TMDB에서 API 키를 저장하거나 .env에 TMDB_API_KEY를 설정하세요."
)
MATCH_COORDINATOR_NO_ROWS_TITLE: Final[str] = "매칭할 항목 없음"
MATCH_COORDINATOR_NO_ROWS_MESSAGE: Final[str] = (
    "먼저 폴더를 스캔하고 제목 읽기가 끝난 뒤 다시 시도하세요."
)
MATCH_COORDINATOR_PROGRESS_TITLE: Final[str] = "TMDB 매칭 중"
MATCH_COORDINATOR_PROGRESS_MESSAGE: Final[str] = "한국어 제목을 TMDB에서 찾고 있습니다…"
MATCH_COORDINATOR_NO_SELECTION_TITLE: Final[str] = "선택 없음"
MATCH_COORDINATOR_NO_SELECTION_MESSAGE: Final[str] = "결과 목록에서 항목을 먼저 선택하세요."
MATCH_COORDINATOR_EMPTY_QUERY_TITLE: Final[str] = "검색어 없음"
MATCH_COORDINATOR_EMPTY_QUERY_MESSAGE: Final[str] = "검색어를 입력하세요."

PLAN_APPLY_EMPTY_TITLE: Final[str] = "항목 없음"
PLAN_APPLY_EMPTY_MESSAGE: Final[str] = "먼저 스캔과 제목 매칭을 완료하세요."
PLAN_APPLY_NO_MATCHED_TITLE: Final[str] = "TMDB 매칭 없음"
PLAN_APPLY_NO_MATCHED_MESSAGE: Final[str] = (
    "TMDB 한국어 제목이 있는 파일이 없습니다. "
    "자동 또는 수동으로 매칭한 뒤 다시 시도하세요."
)
PLAN_APPLY_PATH_RULES_TITLE: Final[str] = "저장 위치 규칙 필요"
PLAN_APPLY_PATH_RULES_MESSAGE: Final[str] = (
    "설정 → 저장 위치 규칙에서 정리할 위치와 폴더 이름 규칙을 지정하세요."
)
PLAN_APPLY_PLAN_PROGRESS_TITLE: Final[str] = "미리보기 준비 중"
PLAN_APPLY_PLAN_PROGRESS_MESSAGE: Final[str] = "이동 경로를 계산하고 있습니다…"
PLAN_APPLY_PLAN_ERROR_TITLE: Final[str] = "미리보기 오류"
PLAN_APPLY_DRY_RUN_TITLE: Final[str] = "미리보기"
PLAN_APPLY_DRY_RUN_EMPTY_MESSAGE: Final[str] = "이동할 파일이 없습니다."
PLAN_APPLY_EXECUTE_UNAVAILABLE_TITLE: Final[str] = "파일 이동 불가"
PLAN_APPLY_EXECUTE_UNAVAILABLE_MESSAGE: Final[str] = (
    "파일 이동 기능을 사용할 수 없습니다. 앱을 다시 실행해 주세요."
)
PLAN_APPLY_LOG_ROOT_TITLE: Final[str] = "기록 경로"
PLAN_APPLY_LOG_ROOT_MESSAGE: Final[str] = "스캔 폴더 또는 정리할 위치를 먼저 설정하세요."
PLAN_APPLY_MOVE_PROGRESS_TITLE: Final[str] = "파일 이동 중"
PLAN_APPLY_MOVE_PROGRESS_MESSAGE: Final[str] = "이동 중…"
PLAN_APPLY_MOVE_ERROR_TITLE: Final[str] = "이동 오류"
PLAN_APPLY_COMPLETE_TITLE: Final[str] = "완료"
PLAN_APPLY_COMPLETE_MESSAGE_TEMPLATE: Final[str] = "{moved_count}개 파일을 이동했습니다."
