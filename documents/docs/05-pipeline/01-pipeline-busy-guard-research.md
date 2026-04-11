# Research: 파이프라인 중복 실행 방지

## 날짜

2026-04-10

## 관찰

1. **스레드 등록 불일치**: `scan_parse_coordinator`만 `register_worker_thread`로 `_worker_threads`에 등록한다. 매칭·플랜·적용·(기존) TMDB 검색은 `update_current_worker_thread`만 호출해 목록 추적이 되지 않았다.
2. **시그널 순서**: `UseCaseWorker`는 `result.emit` 후 `finished.emit`한다. 적용 완료 직후 동기적으로 `on_scan_clicked`를 호출하면 이전 `QThread`가 아직 `isRunning()`일 수 있어, “리스트 비움”만으로는 부족하다. 내부 재스캔은 사용자 가드 없이 별도 진입점으로 분리한다.
3. **판별**: `has_active_pipeline_work()`는 `any(t.isRunning() for t in _worker_threads)`로 통일한다. 모든 워커는 `register_worker_thread`로 등록한다.

## 결론

- `register_worker_thread` 단일화 + 등록/종료 시 액션 바 `refresh`.
- 사용자 트리거(스캔/매칭/Dry Run)에 진입 가드.
- `FolderScanBar`에 `set_pipeline_busy`로 스캔·매칭 비활성화, Dry Run은 `dry_run_should_enable() and not busy`.
