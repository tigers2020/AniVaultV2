# Settings 탭형 레이아웃 전환 구현 플랜

작성일: 2026-04-10

## 목표
- Settings 화면의 카드형 설정을 3개 탭으로 묶어 가독성과 탐색성을 높인다.
- 저장/로드/리셋 및 auto-save 동작은 유지한다.

## 구현 항목
1. `settings_page.py`
- `QTabWidget` 기반 레이아웃으로 전환한다.
- 액션 카드는 최상단 공통 영역에 둔다.
- 탭별 컨테이너 생성 helper를 추가해 조립 책임을 분리한다.

2. 탭 구성
- `General`: `ScanBuildCard`, `AppearanceCard`
- `Paths`: `PathRulesForm`
- `Parse & TMDB`: `ParseTmdbForm`

3. 테스트
- Settings 페이지 constructor 테스트를 탭 구조 기준으로 갱신한다.
- 액션 카드의 상단 고정과 탭별 카드 배치를 확인한다.

## 검증
- `pytest`
- `ruff check .`
- `mypy src`
- `black .`
