# Constants Consolidation Research

- `src/anivault/` 전역에 숫자 기본값, 상태 문자열, GUI 문구, 환경 변수 이름, 경로/파일명 기본값이 분산되어 있었다.
- 이미 로컬 상수로 선언된 값도 많았지만 정의 위치가 제각각이라 단일 출처가 아니었다.
- 정리 기준은 `src/anivault/constants/` 아래에 `domain`, `application`, `adapters`, `gui` 서브패키지를 두고 같은 의미의 고정값을 해당 레이어 상수로 이동하는 것이다.
- `domain/rules/*`처럼 계산, 정규화, 조합 책임이 있는 함수형 규칙 모듈은 유지 대상으로 보고 단순 값 상수만 이동 대상으로 취급한다.
- 2차 검토에서 operation log, SQLite 저장소의 batch/status, GUI 폼과 테이블의 로컬 copy/config를 정리했다.
- 3차 검토에서 `ffprobe` 명령 shape, GUI 하위 organism/molecule copy, `scan_parse_coordinator`의 내부 튜닝 값, `sqlite_parse_cache_repository`의 read 경로 status 비교를 정리했다.
- 이번 단계에서 실제 앱 흐름에 쓰이는 settings form 2개와 dialog 2개의 header/label/placeholder/button copy를 `constants/gui/components.py`로 이동했다.
- 현재 남은 우선 GUI 구간은 `path_select_field.py`의 공용 버튼 문구와 `pipeline_result_panel.py`의 상태 라벨이다. 그 이후 `details_pane.py` 같은 실제 앱 흐름 organism/template를 계속 훑는 순서가 자연스럽다.
