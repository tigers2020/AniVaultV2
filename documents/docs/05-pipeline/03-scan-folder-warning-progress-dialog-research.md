# scan-folder-warning-progress-dialog research

## 요청
- 스캔 폴더가 비어 있거나 사용할 수 없을 때는 경고창만 떠야 하는데, 진행 중 다이얼로그도 보인다는 제보를 확인했다.

## 확인한 코드
- `src/anivault/interfaces/gui/presenters/organizing/scan_parse_coordinator.py`
  - `on_scan_clicked()`는 빈 경로와 잘못된 경로를 먼저 검사하고, 이 경우 `_start_scan_worker()`를 호출하지 않고 즉시 반환한다.
  - 실제 진행 다이얼로그는 `_start_scan_worker()` 내부에서 `run_use_case_worker_with_progress_dialog()`를 통해서만 표시된다.
- `src/anivault/interfaces/gui/presenters/worker_session.py`
  - 진행 다이얼로그는 worker `started` 시그널에서 `show_progress()`로 열린다.
- `src/anivault/interfaces/gui/components/molecules/progress_dialog.py`
  - 공유 `ProgressDialog`는 `hide_progress()`가 호출되어야만 숨겨진다.
  - 빈 경로/잘못된 경로의 early return 경로에서는 다이얼로그 정리 로직이 없다.
- `tests/unit/interfaces/gui/test_scan_parse_coordinator.py`
  - 빈 경로/잘못된 경로에서 경고가 뜨고 실행 함수가 호출되지 않는 테스트는 이미 있다.
  - 하지만 "기존 progress dialog가 열려 있을 때 early return이 dialog를 숨기는지"에 대한 회귀 테스트는 없다.

## 현재 진단
- 새 스캔 작업이 빈 경로에서 시작되는 직접 증거는 코드상 보이지 않았다.
- 대신 공유 progress dialog가 이전 상태를 유지한 채 남아 있으면, 경고창과 함께 progress dialog가 동시에 보일 수 있다.
- 따라서 수정 포인트는 `on_scan_clicked()`의 빈 경로/잘못된 경로 guard에서 stale progress dialog를 명시적으로 숨기거나 세션을 정리하는 쪽이 가장 자연스럽다.

## 영향 범위
- GUI presenter/coordinator (`interfaces/gui/`) 한 파일 중심.
- 단위 테스트 1건 이상 추가 필요.
- domain/application/adapters 영향은 없어 보인다.
