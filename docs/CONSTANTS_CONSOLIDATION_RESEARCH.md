# Constants Consolidation Research

- `src/anivault/` 전역에 숫자 기본값, 상태 문자열, GUI 문구, 환경 변수 이름, 경로/파일명 기본값이 분산되어 있었다.
- 이미 로컬 상수로 선언된 값도 많았지만 정의 위치가 제각각이라 단일 출처가 아니었다.
- 정리 기준은 `src/anivault/constants/` 아래에 `domain`, `application`, `adapters`, `gui` 서브패키지를 두고 같은 의미의 고정값을 해당 레이어 상수로 이동하는 것이다.
- `domain/rules/*`처럼 계산, 정규화, 조합 책임이 있는 함수형 규칙 모듈은 유지 대상으로 보고 단순 값 상수만 이동 대상으로 취급한다.
- 2차 검토에서 operation log, SQLite 저장소의 batch/status, GUI 폼과 테이블의 로컬 copy/config를 정리했다.
- 이번 3차 검토에서는 `ffprobe` 명령 shape, GUI 하위 organism/molecule copy, `scan_parse_coordinator`의 내부 튜닝 값, `sqlite_parse_cache_repository`의 read 경로 status 비교를 다음 누락으로 확인했다.
- SQL 본문은 각 저장소에 남기되, 상태 문자열과 기본 limit/chunk 값, 실행 인자 shape, 사용자 문구는 `constants`를 단일 출처로 삼는 쪽이 현재 구조와 가장 잘 맞는다.
