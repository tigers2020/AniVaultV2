---
title: GUI 사용자 중심 문구 전면 개편 플랜
status: approved
approved_by: "user-request 2026-04-11"
---

# GUI 사용자 중심 문구 전면 개편 플랜

## 용어 기준표 (확정)

| 개념(기존) | 한국어 | 영어 |
|------------|--------|------|
| Organizer | 정리 작업 | Organize |
| Main Views | 화면 | Sections |
| Pipeline result | 작업 결과 | Results |
| Parse / Parsed Title | 파일명에서 읽은 제목 | Title from filename |
| Parse group / Parse Title Group | 제목 그룹 | Title group |
| TMDB Korean Title Group | TMDB 한국어 제목 | TMDB Korean title |
| Path rules | 저장 위치 규칙 | Folder rules |
| Target root / Target root folder | 정리할 위치 | Destination folder |
| Path template | 폴더 이름 규칙 | Folder name pattern |
| Dry run | 미리보기 | Preview |
| Apply move | 이동 실행 | Move files |
| Pipeline controls | 작업 단계 | Workflow |
| Scan and build plan | 폴더 스캔 | Scan folders |
| Execution | 파일 이동 | Move files |
| Parse & TMDB | 파일명 및 TMDB | Filenames & TMDB |
| Ignore tokens | 무시할 단어 | Ignore tokens |
| Season folder format | 시즌 폴더 형식 | Season folder format |
| Unknown resolution | 해상도 미확인 시 | Fallback resolution |
| Unknown group folder | 그룹 미확인 시 폴더 | Fallback group folder |

유지: TMDB, AniVault, 파일/폴더 등 실체가 있는 개체명.

## 적용 범위

### i18n locale (주 대상)

| 파일 | 작업 |
|------|------|
| `locales/fragments.py` | `DRY_RUN_EN` → `"Preview"`, `PARSED_TITLE_EN` → `"Title from filename"` |
| `locales/en.py` | 전체 MESSAGES 값을 product copy로 재작성 |
| `locales/ko.py` | 전체 MESSAGES 값을 자연스러운 한국어로 재작성, 잔여 영문 제거 |

### 하드코딩

| 파일 | 문자열 | 변경 |
|------|--------|------|
| `poster_card.py` | `"Poster"` / `"Backdrop"` placeholder | 사용자형 문구로 교체 |
| `poster_grid.py` | `pill_text="Poster Grid"` | 사용자형 문구로 교체 |

### constants 동기화

| 파일 | 범위 |
|------|------|
| `copy.py` | `PAGE_META`, `SIDEBAR_TITLE`, `PIPELINE_RESULT_*` 등 표시 문자열 |
| `components.py` | `PIPELINE_RESULT_PANEL_*`, 스캔/설정 카드 헤더 등 표시 전용 상수 (상태 저장 상수 값은 유지) |

## 테스트 영향

| 테스트 파일 | 갱신 필요 항목 |
|-------------|---------------|
| `test_i18n_service.py` | `"Subtitles only"` → 새 en 값, `"Scanned"` → 새 en 표시 문구 |
| `test_plan_apply_coordinator.py` | `["Dry Run"]` / `["플랜 오류"]` → 새 문구 |
| `test_widget_smoke.py` | `PanelHeader("Organizer", ...)`, `"Organizer" in label_texts` → 새 라벨 |
| `test_app_main_page_settings_presenter.py` | `PAGE_ORGANIZER_TITLE: "Organizer"` mock → 새 문구 |
| `test_env_file.py` | `PAGE_META["subtitles"]` 기대값 |
