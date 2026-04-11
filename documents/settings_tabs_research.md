# Settings 탭형 레이아웃 전환 조사

작성일: 2026-04-10

## 현황
- Settings 화면은 [settings_page.py](F:\Python_Projects\AniVault_V2\src\anivault\interfaces\gui\pages\settings_page.py)에서 직접 조립한다.
- 현재 구조는 `QScrollArea` 안에 `QGridLayout` 하나를 두고 아래 위젯을 2열로 배치한다.
- 공통 액션: `SettingsActionsCard`
- 일반 설정: `ScanBuildCard`, `AppearanceCard`
- 규칙 설정: `PathRulesForm`, `ParseTmdbForm`

## 코드 경계
- 조립 책임은 `interfaces/gui/pages/settings_page.py`에 모여 있다.
- 저장/로드 책임은 [settings_presenter.py](F:\Python_Projects\AniVault_V2\src\anivault\interfaces\gui\presenters\settings_presenter.py)가 맡고 있다.
- presenter는 `set_forms(path_rules_form, parse_tmdb_form, scan_build_card)`만 알면 되므로, 위젯 배치 변경은 presenter API 수정 없이 처리 가능하다.

## 영향 범위
- 필수 변경:
  - Settings 페이지 조립 코드
  - Settings 페이지 constructor 테스트
- 비필수 변경:
  - 각 카드 내부 로직
  - settings 저장 포맷
  - presenter save/load/reset 흐름

## 결정
- Settings 상단의 `Save / Reset / Load` 액션 카드는 탭 바깥 공통 영역에 유지한다.
- 탭은 3개로 나눈다.
  - `General`: `ScanBuildCard`, `AppearanceCard`
  - `Paths`: `PathRulesForm`
  - `Parse & TMDB`: `ParseTmdbForm`
- 기존 `QScrollArea`는 유지한다.
- 탭 내부 레이아웃은 기존 theme spacing 값을 재사용한다.
