# Plan: 파이프라인 중복 실행 방지 (승인됨)

## 범위

- `OrganizerPresenter.has_active_pipeline_work` + `refresh_pipeline_action_bar_state`
- 코디네이터: `register_worker_thread` 통일, 사용자 가드, 적용 후 재스캔은 `run_scan_after_apply_completion`
- `FolderScanBar.set_pipeline_busy`, `organizer_page` 연결
- TMDB 수동 검색: 파이프라인 busy 시 시작 차단
- 단위 테스트 및 검증 파이프라인

## 승인

구현 단계 진행 (사용자 요청으로 승인 간주).
