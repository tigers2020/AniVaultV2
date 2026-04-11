# scan-folder-warning-progress-dialog plan

## 목표
- 스캔 폴더가 비어 있거나 사용할 수 없는 경우에는 경고창만 남기고, 공유 progress dialog가 보이지 않도록 만든다.

## 변경 범위
- `src/anivault/interfaces/gui/presenters/organizing/scan_parse_coordinator.py`
- `tests/unit/interfaces/gui/test_scan_parse_coordinator.py`

## 접근
1. `on_scan_clicked()`의 early return 분기(빈 경로, 잘못된 경로)에서 현재 presenter의 `ProgressDialog`가 존재하면 stale 표시 상태를 정리하는 헬퍼를 추가한다.
2. 실제 워커를 시작하는 정상 경로는 그대로 두고, guard 분기에서만 dialog 정리를 수행한다.
3. 단위 테스트를 추가해 빈 경로 또는 잘못된 경로에서 경고 후 `hide_progress()`가 호출되는지 검증한다.

## 트레이드오프
- 장점: 공유 dialog의 남은 표시 상태를 빠르게 정리해 사용자 체감 버그를 직접 막을 수 있다.
- 주의: 정상적으로 진행 중인 다른 작업의 dialog를 숨기면 안 되므로, guard 분기에서만 최소 범위로 호출해야 한다.

## 검증 계획
- `pytest tests/unit/interfaces/gui/test_scan_parse_coordinator.py`
- 가능하면 `pytest`
- `ruff check .`
- `mypy src`
- `black .`

## 승인 요청
- 이 계획 기준으로 구현을 진행해도 되는지 확인이 필요하다.
