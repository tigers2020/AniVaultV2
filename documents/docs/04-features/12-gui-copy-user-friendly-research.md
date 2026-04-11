---
title: GUI 사용자 노출 문구 인벤토리 및 문제 유형 분류
status: research
---

# GUI 노출 문구 리서치

## 범위

`src/anivault/interfaces/gui/i18n/locales/en.py`, `ko.py`, `fragments.py`에 정의된 약 230개 MESSAGES 엔트리와
`constants/gui/copy.py`, `components.py`의 표시 전용 상수를 대상으로 한다.

## 문제 유형 분류

### 1. 내부 단계명이 그대로 노출

| 키(대표) | 현재 문구 | 문제 |
|----------|----------|------|
| `SHELL_TAB_ORGANIZER` | Organizer | 내부 모듈명 |
| `ORG_PIPELINE_HEADER_TITLE` | Pipeline result (en) / 파이프라인 결과 (ko) | pipeline은 사용자 언어가 아님 |
| `SETTINGS_SCAN_BUILD_PILL` | Pipeline controls / 파이프라인 제어 | 동일 |
| `ORG_PLAN_PLAN_PROGRESS_TITLE` | Building plan / 플랜 생성 | plan은 내부 개념 |
| `ORG_PLAN_DRY_RUN_TITLE` | Dry Run | 기술 용어 |

### 2. ko 카탈로그에 영문 잔재

| 키 | 현재 ko 값 |
|----|-----------|
| `SHELL_SIDEBAR_TITLE` | Main Views |
| `SHELL_TAB_ORGANIZER` | Organizer |
| `SHELL_TAB_SETTINGS` | Settings |
| `PAGE_ORGANIZER_TITLE` | Organizer |
| `PAGE_ORGANIZER_DESC` | 영문 문장 그대로 |
| `PAGE_SETTINGS_TITLE` | Settings |
| `PAGE_SETTINGS_DESC` | 영문 문장 그대로 |
| `SETTINGS_APPEARANCE_HEADER_TITLE` | Appearance |
| `SETTINGS_APPEARANCE_HEADER_PILL` | Theme |
| `SETTINGS_APPEARANCE_THEME_LABEL` | Theme |
| `SETTINGS_APPEARANCE_LANGUAGE_LABEL` | Language |
| `TBL_*` 대부분 | 영문 헤더 |
| `DETAILS_LBL_PARSED` | Parsed Title |
| `DETAILS_LBL_PARSE_GROUP` | Parse Group |
| `DETAILS_LBL_YEAR_SEASON_EP` | Year / Season / Ep |
| `CONTENT_LBL_PARSED` | Parsed |
| `SETTINGS_PATH_LABEL_*` | 영문 |
| `SETTINGS_PARSE_LBL_*` | 영문 |
| `SETTINGS_ACTIONS_CARD_TITLE` | Settings |
| `SETTINGS_ACTIONS_CARD_PILL` | Actions |
| `SETTINGS_SCAN_BUILD_SOURCE_PH` | Source: G:/... |
| `ORG_SCANBAR_BTN_DRY_RUN` | Dry Run |

### 3. 기술 설정 직역 / 사용자 맥락 부족

| 키 | 현재 문구 | 문제 |
|----|----------|------|
| `SETTINGS_PATH_RULES_TITLE` | Path rules / 경로 규칙 | 무엇의 규칙인지 불분명 |
| `SETTINGS_PARSE_TITLE` | Parse and TMDB rules / Parse 및 TMDB 규칙 | parse의 대상 모호 |
| `SETTINGS_SCAN_BUILD_TITLE` | Scan and build plan / 스캔 및 플랜 빌드 | build plan이 무엇인지 불분명 |
| `ORG_STAT_PARSED_TITLES` | Parsed titles / 파싱된 제목 | 무엇을 파싱? |
| `EXEC_CARD_HEADER_TITLE` | Execution / 실행 | 무엇을 실행? |

### 4. 경고·오류에 다음 행동 미안내

대부분의 오류 메시지는 이미 다음 행동을 포함하고 있어 양호하나,
`ORG_PLAN_LOG_ROOT_MESSAGE`("Set scan source path or Target root")처럼
Target root 같은 기술 용어가 섞인 안내가 일부 남아 있다.

### 5. locale 밖 하드코딩

| 파일 | 문자열 | 문제 |
|------|--------|------|
| `poster_card.py` | `"Poster"`, `"Backdrop"` | 이미지 미로드 시 사용자에게 노출 |
| `poster_grid.py` | `pill_text="Poster Grid"` | 패널 헤더 pill |

## 결론

변경 대상은 **en.py·ko.py 전면**, **fragments.py** 공용 조각, **하드코딩 2건**,
그리고 동기화 대상인 **copy.py·components.py** 표시 전용 상수이다.
