# 로컬 보안 재검증 보고 (PR #1 관심 축)

날짜: 2026-04-10  
범위: Codex `find-vulnerabilities` memory가 본 PR #1 축과 동일하게 로컬 트리 재점검.

## 브랜치·원격 정렬

- `origin`: `https://github.com/tigers2020/AniVaultV2.git`
- 작업 트리: `main` … `origin/main` (PR #1 전용 브랜치 미체크아웃; 원격 PR 본문 diff와 1:1 비교는 수행하지 않음)
- 로컬 미커밋 변경 존재: i18n, `pipeline_result_panel.py`, 테마, 관련 테스트, `interfaces/gui/utils/` 등 — 본 검토는 플랜에 명시된 **앵커 파일** 중심

## 검토한 경로 목록

| 경로 | 초점 |
|------|------|
| `src/anivault/interfaces/gui/services/image_loader.py` | 로컬 `file:`/절대 경로, `http` 원격 GET, 중복 요청 억제 |
| `src/anivault/interfaces/gui/settings_storage.py` | JSON 로드, 키 화이트리스트, 시크릿 키 저장 제외 |
| `src/anivault/application/use_cases/match_series.py` | 매칭 use case 경계(포트·취소 토큰) |
| `src/anivault/interfaces/gui/presenters/organizing/manual_tmdb_relay.py` | 슬롯·UI 갱신 |
| `src/anivault/interfaces/gui/presenters/organizing/match_coordinator.py` | 워커·QueuedConnection |
| `src/anivault/interfaces/gui/presenters/organizing/scan_parse_coordinator.py` | 워커·스캔/파싱 경계(상단·워커 패턴) |
| `src/anivault/domain/rules/tmdb_image_url.py` | CDN URL 조립 |
| `src/anivault/domain/rules/poster_remote_path.py` | 상대 경로 정규화 |
| `src/anivault/interfaces/gui/presenters/row_mapper.py` | `poster_url` 결정 |
| `src/anivault/adapters/persistence/sqlite/sqlite_parse_cache_repository.py` | SAVEPOINT 이름 |
| `src/anivault/adapters/persistence/sqlite/sqlite_library_index_repository.py` | 동적 `IN (?)` + params |
| `src/anivault/adapters/persistence/sqlite/sqlite_title_match_repository.py` | f-string `execute` 없음(샘플) |

## 정적 보조 스캔

- `pickle` / `eval(` / `yaml.unsafe_load` / `shell=True`: **해당 없음** (Qt `*.exec()` 등은 제외)
- `subprocess`: `adapters/media/ffprobe_stream_resolution.py` — 인자 리스트 기반, `shell` 미사용
- SQLite: `f"SAVEPOINT …"` 는 `sqlite_parse_cache_repository` 내 **상수** 세이브포인트명에 한함

## 데이터 흐름 (포스터·백드롭 URL)

- CDN 조립: `tmdb_poster_cdn_url` / `tmdb_backdrop_cdn_url` — 상대 경로는 `https://image.tmdb.org/t/p/{size}{path}` 로 고정 호스트
- API가 이미 `http…` 절대 URL을 주면 **그대로 통과** (`normalize_tmdb_remote_image_path` strip만) → `ImageLoader` 가 `startswith("http")` 로 원격 로드 가능. 위협은 주로 **오염된 메타데이터/DB 값** 가정 시 이론적(단일 사용자 데스크톱 앱 맥락에서 낮음).

## 설정 (`settings_storage`)

- `json.loads` 만 사용; `parse_tmdb` 저장 시 `PARSE_TMDB_SECRET_KEYS` 제외
- 병합은 `PATH_RULES_KEYS`, `PARSE_TMDB_KEYS`, `SCAN_BUILD_*` 등 **허용 키** 위주

## Qt·스레딩

- `match_coordinator._run_tmdb_search_worker`: `ManualTmdbSearchRelay` 슬롯을 `Qt.ConnectionType.QueuedConnection` 으로 연결 → 워커 결과·에러가 메인 스레드 큐로 전달

## 심각도별 findings

| 심각도 | 내용 |
|--------|------|
| **Critical / High / Medium** | **없음** (이번 로컬 패스 기준) |
| **Low / 정보** | `manual_tmdb_relay.on_error`: `QMessageBox.warning(..., str(exc))` — 사용자에게 스택/내부 메시지 노출 가능(민감도 낮음). |
| **Low (이론)** | TMDB/캐시가 비정상 절대 `http(s)` 이미지 URL을 넣으면 `ImageLoader` 가 해당 URL로 GET — 신뢰 경계는 외부 API·로컬 DB. |

## 수정·후속 (fix-gate)

- 2026-04-10 후속: Low 항목 완화를 위해 (1) 수동 TMDB 검색 오류는 로그에 `exc_info` 저장·UI는 i18n 고정 문구, (2) `tmdb_*_cdn_url` 절대 URL은 `image.tmdb.org`만 허용하도록 제한. 상세는 해당 모듈 커밋/테스트 참고.

## 결론

PR #1 자동화 결론과 정합: 동일 축에 대해 로컬에서도 **중·고·치명도 취약점은 발견하지 않음**. 위 표의 Low 항목은 운영·UX 차원의 선택적 하드닝 후보.
