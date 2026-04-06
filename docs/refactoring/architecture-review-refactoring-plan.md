# 아키텍처 리뷰 기반 리팩터링 실행 계획

**문서 위치**: `docs/refactoring/architecture-review-refactoring-plan.md`  
함수명·줄 번호는 구현 직전 로컬 코드와 한 번 더 대조하는 것이 안전합니다.

**진행 상황 요약 (동기화)**: **P0는 코드 기준으로 완료.** P1-A / P1-B / P2는 미착수. 아래 [진행 상황](#진행-상황) 표 참고.

---

## 진행 상황

| 구간 | 상태 | 비고 |
|------|------|------|
| **P0-1** 팩토리 통합 | 완료 | `create_organizer_page`, `mode="video"` 또는 `mode="subtitle"` 단일 공개 팩토리. `create_subtitle_organizer_page`는 제거됨. `app.py`는 `mode`만 구분해 호출. |
| **P0-2** Presenter 분해 | 완료 | `OrganizerPresenter`는 facade. `presenters/organizing/`에 `ScanParseCoordinator`, `MatchCoordinator`, `PlanApplyCoordinator`, `ManualTmdbSearchRelay`. |
| **P0-3** Panel 분해 | 완료(1차) | `templates/pipeline_selection_sync.py`(분할↔통합 선택), `templates/poster_view_binder.py`(이미지 로드·미리보기), `restore_pipeline_result_panel_ui_state` in `pipeline_result_ui_state.py`(복원 순서). 패널에는 레이아웃·그리드 lazy·`_sync_views_from_model` 등이 남음(추가 얇히기는 P1-B 등과 별도 검토). |
| **P1-A** | 대기 | `worker_session` 등 |
| **P1-B** | 대기 | `modelReset` 완화, `match_series` 병렬화 검토 |
| **P2** | 대기 | dead API, autoscan, ImageLoader dedupe, pyproject 메타 |

**관련 단위 테스트 (일부)**: `tests/unit/interfaces/gui/test_composition_organizer_factory.py`, `test_organizer_presenter_facade.py`, `test_pipeline_selection_sync.py`, `test_poster_view_binder.py`, `test_pipeline_result_panel_state.py`(복원 순서·카드 재클릭 등).

---

## 목적

AniVault V2의 현재 구조에서 가장 큰 리스크는 기능 부족보다 **책임 집중, 중복, 구조 경직**입니다.  
이번 리팩터링의 목표는 다음 4가지입니다.

1. 조립 코드와 UI orchestration의 결합도 축소
2. Presenter/Panel의 God Object 성향 완화
3. 중복 제거로 변경 누락 위험 축소
4. 이후 기능 추가가 쉬운 구조 확보

---

## 리팩터링 호환층 (중간 전략)

**원칙**: 단계마다 **공개 표면을 동결**하고 내부만 이동해 UI wiring 깨짐을 막는다.

1. **1단계** — `OrganizerPresenter`의 public slot/시그니처 유지, 구현은 Coordinator·헬퍼에 위임. `OrganizerPage` / `app.py` 변경은 최소.
2. **2단계** — 단위 테스트·GUI 스모크 통과 후, 사용되지 않는 private만 정리. public API 축소는 별도 합의 없이 하지 않음.
3. **3단계** — dead public 제거·이름 변경은 호출부 전수 검색 후 일괄.
4. **`PipelineResultPanel`** — Presenter 분해와 동시에 대수술하지 않고, P0-3의 단계적 분해(helper → 얇은 본체 → 선택적 파일 분리)를 따름.

---

## 우선순위 요약

| 우선순위 | 목표 | 핵심 대상 |
|----------|------|-----------|
| P0 | 구조 분해와 팩토리 통합 | `composition.py`, `organizer_presenter.py`, `pipeline_result_panel.py` |
| P1-A | 반복 제거와 단일 출처 정리 | worker 실행 패턴, SQL 상수 |
| P1-B | 성능/동작 정책 재검토 | `modelReset`, `match_series` 병렬화 |
| P2 | dead surface 및 UX 정책 정리 | autoscan, dead 메서드, `ImageLoader`, `pyproject.toml` |

---

# P0 — 구조 분해·공장 통합

## P0-1. `composition.py` 팩토리 통합

**상태: 완료**

### 대상

- `create_organizer_page`(`mode` 인자)
- ~~`create_subtitle_organizer_page`~~ — **제거됨**(호출부 없음)
- `app.py`의 호출부

### 목표

비디오/자막 페이지 생성 로직을 하나의 팩토리로 수렴한다.

### 구현 방향

예시:

- `create_organizer_page(..., mode="video" | "subtitle")`
  또는
- `create_organizer_page(..., scan_extensions=..., include_companion_subtitles=...)`

### 유지할 차이점

- subtitle mode는 `SUBTITLE_SCAN_EXTENSIONS`
- subtitle mode는 `include_companion_subtitles=False`

### 완료 기준

- organizer/subtitle page 생성 public factory가 1개로 수렴
- `app.py`에서는 mode 또는 설정값만 바꿔 호출
- 비디오 탭과 자막 탭 모두 기존과 동일하게 기동/스캔 가능

### 리스크

- subtitle mode 전용 설정이 통합 과정에서 누락될 수 있음

---

## P0-2. `OrganizerPresenter` 분해

**상태: 완료**(coordinator·relay는 `src/anivault/interfaces/gui/presenters/organizing/`)

### 목표

외부 public API는 유지하면서, 내부 책임을 coordinator로 분리한다.

### 원칙

- `OrganizerPage`가 사용하는 `OrganizerPresenter`의 외부 시그니처는 최대한 유지
- 1차는 내부 위임 구조 도입
- 2차에서 불필요 private 메서드 정리

### 분해안

#### 1) `ScanParseCoordinator`

담당:

- scan worker 시작
- parse worker 시작
- progress session 처리
- scan result → pipeline row 변환
- parse result 병합
- sync title groups 호출

#### 2) `MatchCoordinator`

담당:

- TMDB 자동 매칭
- match result → pipeline row 변환
- 수동 TMDB 매칭 dialog orchestration
- manual match 후 model 반영

#### 3) `PlanApplyCoordinator`

담당:

- dry-run 실행
- plan 생성/적용
- apply 후 재스캔 정책
- dry-run 버튼 enable 상태 관리

#### 4) `ManualTmdbSearchRelay`(구현됨)

담당:

- TMDB 수동 검색 대화상자 전용 relay(`manual_tmdb_relay.py`)

### 완료 기준

- `OrganizerPresenter`는 facade 역할만 수행
- worker orchestration, TMDB dialog, dry-run/apply 흐름이 별도 coordinator로 분리
- Presenter 본문 길이와 private method 수가 유의미하게 감소
- 기존 UI wiring 변경 없이 동작 유지

### 리스크

- progress dialog token/session 정리가 coordinator 분리 중 꼬일 수 있음

---

## P0-3. `PipelineResultPanel` 분해

**상태: 완료(1차)** — 핵심 로직은 아래 모듈로 이전. 패널은 여전히 스플리터·그리드·`modelReset` 동기화 등 레이아웃·오케스트레이션을 담당.

### 목표

`PipelineResultPanel`을 레이아웃 중심 템플릿으로 되돌리고,  
상태/선택/포스터 처리를 외부 helper 또는 controller로 분리한다.

### 분리 대상

#### 1) UI 상태 저장/복원

대상:

- 정규화·저장: `pipeline_result_ui_state.py`(`normalize_pipeline_ui_state`, `persist_pipeline_results_ui_state` 등)
- 복원 순서: `restore_pipeline_result_panel_ui_state`(패널은 `_restore_ui_state`에서 콜백만 전달)
- `_persist_ui_state`는 패널에 얇은 래퍼로 유지(위젯 값 수집 → `persist_pipeline_results_ui_state`)

#### 2) 선택 동기화

구현: `templates/pipeline_selection_sync.py` — `unified_index_for_group`, `sync_split_tables_selection`, `on_split_table_selection`.  
패널: 분할 테이블 시그널은 위 모듈 호출, 통합 선택·상세/미리보기 갱신은 `_apply_unified_selection` / `_on_selection`에 잔류.

#### 3) 포스터/이미지 처리

구현: `templates/poster_view_binder.py` — `PosterViewBinder`(URL→카드 매핑, `loaded`, 미리보기 pending).  
패널에 잔류: `_ensure_poster_grid_for_view_key`, `_clear_all_poster_grids`(그리드 위젯 구성·lazy dirty).

### 구현 순서

- 1차: helper/controller 추출
- 2차: panel 본문에서 위임만 남기기
- 3차: 필요시 파일 재배치

### 완료 기준

- 선택 동기화·포스터 로드/미리보기 바인딩·복원 순서의 **핵심 로직**은 모듈로 분리됨
- panel은 레이아웃·시그널 연결·그리드 lazy·`modelReset` 동기화·통합 선택 시 패널 위젯 갱신 등을 유지(완전한 “위젯만” 수준은 P1-B 등과 연계 시 추가 축소 가능)
- 현재 선택/상세 패널/미리보기 패널 동작이 유지됨(회귀 테스트로 일부 검증)

### 리스크

- selection restore와 details/preview pane 토글 동작이 분리 과정에서 깨질 수 있음

---

# P1-A — 반복 제거·단일 출처 정리

## P1-A-1. worker 실행 템플릿 공통화

### 대상

`OrganizerPresenter` 및 coordinator 내부의 반복되는 worker 실행 패턴

### 공통화 대상

- `WorkerSignals()`
- `UseCaseWorker(...)`
- progress dialog 연결
- cancel 연결/해제
- `run_worker(worker)`
- finished cleanup

### 제안

- `presenters/worker_session.py`
- 또는 `run_use_case_worker(...)` helper

### 완료 기준

- scan/parse/match/plan/apply/manual search 흐름에서 중복 보일러플레이트가 감소
- worker lifecycle 처리 방식이 한 군데에서 관리됨

### 리스크

- 공통화 과정에서 특정 worker만 갖는 예외 흐름이 묻힐 수 있음

---

## P1-A-2. `_GROUP_MATCH_UPSERT` 단일화

### 대상

- `sqlite_title_group_repository.py`
- `sqlite_title_match_repository.py`

### 목표

같은 SQL을 한 곳에서 관리한다.

### 제안

- `adapters/persistence/sqlite/sql_queries.py`
  또는
- 전용 상수 모듈

### 완료 기준

- `_GROUP_MATCH_UPSERT` 정의가 1곳만 남음
- 두 repository는 import만 사용

### 리스크

- SQL 이동 후 import path 누락 또는 circular import 가능성

---

# P1-B — 성능/동작 정책 재검토

## P1-B-1. `modelReset` / 전체 재동기화 완화

### 대상

- `PipelineResultPanel._sync_views_from_model`
- `PipelineTableModel.set_rows` / `PipelineResultPanel.set_rows`

### 목표

가능한 경우 전체 재구성 대신 증분 갱신으로 전환한다.

### 방향

- 작은 변경은 `dataChanged` 또는 부분 갱신 검토
- 큰 변경만 `modelReset`
- grid/card 생성은 lazy 전략 유지 및 확장

### 완료 기준

- 단순 상태 변경에서 전체 뷰 재생성이 줄어듦
- 대량 row 상황에서 UI hitch 완화 방향이 확인됨

### 리스크

- 부분 갱신 전략이 잘못 들어가면 선택 상태 sync가 더 복잡해질 수 있음

---

## P1-B-2. `match_series` 병렬화 재검토

### 대상

- `ThreadPoolExecutor` 사용 구간

### 목표

복잡도 대비 실효성이 낮다면 단순화한다.

### 검토 기준

- TMDB request interval lock
- SQLite shared connection + lock
- 실제 체감 성능
- 디버깅 복잡도

### 선택지

- worker 수 조정
- 직렬화 단순화
- 병렬 유지하되 제한 강화

### 완료 기준

- 병렬 유지/축소/제거 중 하나를 명확히 결정
- 근거는 측정 또는 코드 구조 분석으로 남김

### 리스크

- 성능보다 구조 단순화만 보고 제거하면 실제 대량 데이터에서 느려질 수 있음

---

# P2 — 정리·UX 정책·소규모 강화

## P2-1. dead API 정리

### 대상

- `OrganizerPresenter.on_parse_clicked`
- `OrganizerPresenter.on_build_plan_clicked`

(`settings_presenter.py`의 동명 메서드와 혼동하지 말 것.)

### 방향

- 호출부가 없으면 삭제
- 실제 사용할 계획이면 버튼/시그널과 연결 후 구현

### 완료 기준

- `pass` 상태의 dead public surface 제거
- API가 실제 UI 흐름과 일치

---

## P2-2. autoscan 정책 명시화

### 대상

- `OrganizerPage.showEvent`
- apply 후 재스캔 흐름 (`PlanApplyCoordinator` / presenter)

### 목표

스캔 트리거 위치를 예측 가능하게 만든다.

### 제안

- 설정값: 예) `auto_scan_on_first_show` / `scan_build` 하위 키
- 또는 startup flow/controller로 책임 이동

### 완료 기준

- “언제 자동 스캔이 발생하는지” 코드 구조상 명확해짐
- page lifecycle side effect가 줄어듦

---

## P2-3. `ImageLoader` in-flight dedupe

### 대상

- `interfaces/gui/services/image_loader.py`

### 목표

동일 URL에 대한 중복 pending request를 방지한다.

### 완료 기준

- 같은 URL을 연속 요청해도 네트워크 요청은 1회만 유지
- 완료 후 모든 소비자가 동일 결과를 받음

---

## P2-4. `pyproject.toml` 메타 정리

### 목표

패키지 메타데이터와 로드맵/설명성 주석을 분리한다.

### 방향

- phase 설명은 `docs/` 또는 README로 이동
- `pyproject.toml`은 패키징/툴 설정 중심으로 유지

### 완료 기준

- 메타 설정 파일이 현재 상태만 반영
- 로드맵 흔적은 문서로 이동

---

# 구현 순서 권장

1. **P0-1** `composition.py` 통합
2. **P0-2** `OrganizerPresenter` 내부 coordinator 분리
3. **P0-3** `PipelineResultPanel` helper/controller 추출
4. **P1-A** worker helper, SQL 단일화
5. **P1-B** `modelReset` 완화, `match_series` 병렬화 재검토
6. **P2** dead API, autoscan 정책, `ImageLoader`, `pyproject.toml`

---

# 단계별 검증

## 공통 검증

```bash
pytest
ruff check .
mypy src
black .
```

## GUI 스모크 체크

```bash
python -m anivault
```

체크 항목:

- 비디오 탭 스캔
- 자막 탭 스캔
- TMDB 자동 매칭
- 수동 TMDB 매칭
- Dry Run
- Apply
- apply 후 재스캔 동작
- details/preview pane
- view state restore

---

# 추가 테스트 권장

## P0 이후

- ~~composition mode별 factory 구성 테스트~~ → `test_composition_organizer_factory.py` 추가됨
- ~~Presenter facade 유지 테스트~~ → `test_organizer_presenter_facade.py` 추가됨
- manual TMDB match 흐름 테스트(기존 `tests/unit/test_manual_tmdb_match.py` 등 유지·보강 여지)

## Panel 분해 이후

- ~~ui_state restore/persist 테스트~~ → `test_pipeline_result_panel_state.py`(복원 순서·정규화 등)
- ~~selection sync 테스트~~ → `test_pipeline_selection_sync.py`
- ~~동일 카드 재클릭 시 details pane 닫힘 테스트~~ → `test_pipeline_result_panel_state.py` 내 시나리오

## P1 이후

- SQL import 단일화 테스트
- worker helper 공통 경로 테스트
- 병렬/직렬 match 동작 동등성 테스트

---

# 최종 완료 정의

이번 리팩터링은 아래가 만족되면 완료로 본다.

- [x] organizer/subtitle page factory가 단일 구조로 정리됨(**P0 달성**)
- [x] `OrganizerPresenter`가 facade 수준으로 축소됨(**P0 달성**)
- [x] `PipelineResultPanel`이 layout·연결 중심으로 정리되고 선택/포스터/복원 핵심은 모듈 분리됨(**P0 1차 달성**; 추가 축소는 P1-B 등)
- [ ] worker orchestration 중복이 제거됨(**P1-A**)
- [ ] SQL 중복 정의가 사라짐(**P1-A**)
- [ ] autoscan 및 dead API가 정책적으로 정리됨(**P2**)
- [ ] 전체 기능이 기존과 동일하게 동작함(지속 검증: 단위 테스트 + GUI 스모크)

---

## 결론 요약

계획 방향은 유효하다. **P0 구간은 저장소 기준으로 반영 완료**였고, 본 문서는 그에 맞춰 동기화되었다.  
다음 우선 작업은 **P1-A**(worker·SQL 단일화)→ **P1-B** → **P2** 순 권장.  
세부 심볼·줄 번호는 PR·작업 전 로컬 트리와 한 번 더 맞춘다.
