# Constants Consolidation Plan

- `src/anivault/constants/` 패키지를 단일 상수 출처로 유지한다.
- 기존 로컬 상수 정의와 반복 리터럴을 레이어별 상수 모듈로 이동시키고, 호출부는 재정의 대신 `constants` import만 사용하도록 바꾼다.
- GUI 문구와 고정 테이블은 Python 모듈 기반 상수로 통합한다.
- SQL 문장 구조는 유지하고, 상태값·종류값·반복 식별자·batch/chunk 값만 상수 참조로 정리한다.
- 4차 보완 작업:
  - `constants/gui/components.py`에 settings form/dialog 레벨 copy 추가
  - `parse_tmdb_form.py`, `path_rules_form.py`, `tmdb_manual_match_dialog.py`, `dry_run_dialog.py`의 header/label/placeholder/button copy를 상수 참조로 치환
  - 다음 반복 우선순위를 `path_select_field.py` → `pipeline_result_panel.py` → 남은 실제 앱 흐름 GUI 컴포넌트 순으로 고정
