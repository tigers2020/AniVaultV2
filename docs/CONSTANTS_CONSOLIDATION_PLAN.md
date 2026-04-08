# Constants Consolidation Plan

- `src/anivault/constants/` 패키지를 단일 상수 출처로 유지한다.
- 기존 로컬 상수 정의와 반복 리터럴을 레이어별 상수 모듈로 이동시키고, 호출부는 재정의 대신 `constants` import만 사용하도록 바꾼다.
- GUI 문구와 고정 테이블은 Python 모듈 기반 상수로 통합한다.
- SQL 문장 구조는 유지하고, 상태값·종류값·반복 식별자·batch/chunk 값만 상수 참조로 정리한다.
- 3차 보완 작업:
  - `constants/adapters/media.py`에 `ffprobe` CLI shape 상수 추가
  - `constants/gui/components.py` 추가 후 organism/molecule 레벨 copy와 presenter tuning 값 이동
  - `ffprobe_stream_resolution.py`, `execution_card.py`, `folder_scan_bar.py`, `scan_build_card.py`, `settings_action_bar.py`, `scan_parse_coordinator.py` import 치환
  - `sqlite_parse_cache_repository.py` read 경로도 `PARSE_CACHE_STATUS_OK`를 사용하도록 통일
