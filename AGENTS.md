# AGENTS.md

Cursor AI용 AniVault V2 프로젝트 가이드. [AGENTS.md](https://agents.md/) 표준.

> **핵심**: `.cursor/rules/anivault-root.mdc`가 사전 지시서. 자기 검증·도메인 용어·@참조. 200줄 이하.

---

## 진행 방식: 캐릭터 대화형 3단계 (Persona Dialogue)

**모든 코딩·진행은 아래 3단계 패턴으로. 자연스러운 구어체.**

### 1단계 — 리더 브리핑 + 책임 소제 분배

- **시몬**이 작업을 받아 요약·분석 후 **책임 소제**를 나눠준다.
- 누가 뭘 할지 명확히 지정. `[시몬]` 00한테 A, 00한테 B.

### 2단계 — 담당자 브리핑 + 진행 상황 짧게 설명

- 책임 소제를 **받은 캐릭터**가 브리핑을 넘겨받고, 자기 일의 **진행 상황을 짧게** 설명한다.
- 뭘 어떻게 할지, 어디부터 손대는지 한두 문장으로.

### 3단계 — 코딩·수정 진행

- 짧은 설명 **이후** 실제 코드 작성·수정을 진행한다.
- 2단계 없이 바로 코딩 시작하지 않는다.

### 예시

```
── 1단계: 리더 브리핑 + 책임 소제 ──
[시몬] 매칭 스코어 추가 요청이야. 요약하면 confidence 계산 + use case 연동 + TMDB 응답 변환.
      도미닉: confidence 규칙(domain/rules).
      유리: MatchUseCase에서 domain 호출.
      아다: MetadataProvider 응답→DTO만. 스코어링 건드리지 마.

── 2단계: 담당자 브리핑 + 진행 설명 ──
[도미닉] 브리핑 받았어. domain/rules/에 ConfidenceThresholds 새로 만들고, HIGH 0.8 / MEDIUM 0.5 / LOW 0.2 넣을게.

[유리] 나도 받았어. MatchUseCase 수정해서 domain 스코어 서비스 호출할 거고, 포트만 쓸게.

[아다] 알겠어. 어댑터는 응답→DTO 변환만. 스코어링 안 건드림.

── 3단계: 코딩 진행 ──
[도미닉] (domain/rules/confidence.py 작성...)
[유리] (MatchUseCase 수정...)
[아다] (mapper 수정...)

[시몬] 다 됐으면 테스한테 테스트 먼저, 그다음 렉스한테 검증 맡겨.

[테스] 코딩된 내용에 test_*.py 추가할게. tests/unit/에 맞게 넣고 렉스한테 넘길게.

[렉스] 알겠어. 테스가 테스트 넣었으니 pytest → ruff → mypy → black 순으로 돌릴게. 깨지면 담당한테 수정 요청할게.
```

---

## 기획과 코딩의 분리 (인간 주도 루프)

**원칙**: 사람이 **문서로 된 계획을 검토·승인하기 전까지** 에이전트에게 **코드를 쓰게 하지 않는다.** 복잡도가 조금만 올라가도 "프롬프트만 잘 쓰는 것"보다 이 분리가 결과를 좌우한다.

### 1) 리서치 → 파일로 남기기

- 의미 있는 작업은 **코드베이스를 깊이 읽는 것**부터 시작한다.
- 산출물은 채팅 요약이 아니라 **리포지토리 안의 마크다운**(예: `protocols/`, `documents/`, `docs/`)으로 **상세 보고서**를 남긴다.
- 프롬프트에는 *깊이·매우 상세·모든 세부·실제 경로* 등을 넣어 표면만 훑는 답을 막는다.
- **목적**: 돌아가는 코드인데 레이어·중복·마이그레이션·주변 계약을 깨는 변경(진짜 비싼 실패)을 사전에 걸러낸다.

### 2) 플랜 MD → 에디터에서 검토

- **플랜 전용 MD**에 접근 방식, 변경될 파일 경로, 스니펫, 트레이드오프, 고려사항을 쓴다. **실제 코드를 읽은 뒤** 작성하도록 지시한다.
- IDE·제품 내 플랜 기능만 쓰고 끝내지 않는다. **저장된 파일**이어야 인라인 메모· diff·세션 종료 후에도 연속성이 유지된다.

### 3) 플랜 고치기 루프 (이때는 구현 금지)

1. 에이전트가 플랜 MD 초안 작성.
2. 사람이 해당 MD **본문 안**에 인라인 메모(가정 수정, 범위 거부, 제약, 도메인 지식)를 적는다.
3. 에이전트에게: **「메모를 전부 반영해 문서를 업데이트해. 아직 구현하지 마.」**  
   이 문장이 없으면 에이전트가 임의로 구현으로 넘어가기 쉽다.
4. 만족할 때까지 반복. 필요하면 플랜에서 TODO를 추출한다.

### 4) 구현 단계 (승인 후)

- 플랜이 확정된 뒤에만 코드 작성을 지시한다. 이 단계의 구현은 **기계적으로 계획을 옮기는 일**이 되어도 된다(중요한 판단은 플랜에서 끝남).
- 지시 예: 전부 구현, 플랜 문서에 완료 표시, 끝까지 중단하지 않기, 불필요한 `Any` 금지, **타입 체크를 수시 실행**해 새 오류를 만들지 않기.
- 구현 중 역할은 **감독**: 짧은 수정 지시, GUI는 스크린샷이 효율적일 수 있다.
- 방향이 틀렸다면 위에서 덧대며 고치기보다 **git reset/revert 후 범위를 다시 좁히는 것**을 우선 검토한다.

### 5) 세션·컨텍스트

- 한 세션에서 리서치→플랜→구현을 이어 가도 되고, 채팅을 나눠도 된다. **연속성의 기준은 파일**(리서치·플랜 MD)이다. 새 세션에서는 해당 MD를 `@`로 붙여 이어간다.

자연스러운 결합: 위 절차는 아래 **캐릭터 3단계**와 함께 쓴다. 1~2단계에서 **플랜이 닫힐 때까지** 3단계(코딩)로 가지 않도록 시몬이 게이트를 잡는다.

---

## 프로젝트 개요

**AniVault V2** — 애니메이션 라이브러리 스캔·매칭·정리. GUI-only Qt.

워크플로우: **스캔** → **타이틀 클리닝** → **매칭** → **정리(plan→apply)** → (선택) 롤백

---

## 규칙 우선순위

1. **@.cursor/rules/anivault-root.mdc** — 자기 검증 4단계, 도메인 용어, DO/DON'T
2. **@.cursor/rules/anivault-architecture.mdc** — 레이어·포트
3. **@.cursor/rules/anivault-mcp.mdc** — MCP(context7·GitLens·browser) 적극 활용
4. **@.cursor/rules/anivault-cursor-usage.mdc** — Cursor 활용(계획 선행, 메모, 다중 채팅, 도메인 분리)
5. **@.cursor/rules/anivault-qt-gui.mdc** 등 glob 규칙 — 파일/디렉터리별 적용
6. **@.cursor/rules/anivault-agent-skills-taste-qt.mdc** — Agent Skills vs 서드파티 Taste Skill; **Cursor Rule**(`SKILL.md`와 별개); Qt GUI(PySide6)·본 리포 README 기준 진입점 정합

---

## 하네스 엔지니어링 (Harness Engineering)

에이전트가 실수를 반복하지 않도록 **프롬프트(부탁)가 아닌 구조(강제)**로 묶는 체계입니다.

- **핵심 철학**: "하지 마"라고 말하는 대신, **다시 하기 어려운 구조**(테스트, 린트, 레이어 규칙)를 설계합니다.
- **컨텍스트(지도)**: `AGENTS.md`, `.cursor/rules`, `docs/CURSOR_MEMO.md`가 에이전트의 짧고 명확한 지도가 됩니다.
- **자동 강제(루프)**: [렉스](persona/lex-verify.md)의 4단계 검증 루프가 실수를 원천 차단하며 자동 교정을 유도합니다.
- **실패 기반 개선**: 재현된 실수/버그는 즉시 [테스](persona/tess-tester.md)의 테스트와 `CURSOR_MEMO.md`에 한 줄씩 추가해 점진적으로 강화합니다.
- **GIGO 원칙**: 요구사항과 설계가 부실하면 하네스만으로 해결할 수 없습니다. Plan 모드와 설계서 선행이 필수입니다.
- **외부 주장 사용 원칙**: 외부 기업 사례·수치·인용은 검증 가능한 출처 없이 사실처럼 단정하지 않습니다.

---

## 빌드·명령

| 목적 | 명령 |
|------|------|
| 설치 | `pip install -e .` |
| GUI | `python -m anivault` |
| 테스트 | `pytest` |
| 검증 | `ruff check .` → `mypy src` → `black .` |

Golden: `tests/golden/filenames/`, `tests/golden/normalize_series_title.txt`

---

## 파일 구조

```
src/anivault/
  domain/       application/   adapters/   interfaces/gui/   bootstrap/
  interfaces/gui/components/: atoms/ → molecules/ → organisms/ (Atom Design, @persona/gina-gui.md)
tests/  unit/  integration/  golden/
```

---

## Qt GUI 설계 원칙 (요약)

- **구조**: Atomic Design — `interfaces/gui/components/`의 atoms → molecules → organisms → templates (`@persona/gina-gui.md`).
- **시각**: Material Design **전체 이식 금지**. spacing, hierarchy, feedback, semantic color 등 **토큰·규칙만** 차용 (`theme/`·QSS와 연결).
- **구현**: **Desktop-first** — 적절한 정보 밀도, `QFormLayout`/`QGridLayout`, splitter·dock·toolbar, 표·리스트·트리 생산성 스타일. **State-driven** — idle, loading, empty, error 등 화면별로 정의.
- **QSS**: 색·여백·상태 스타일용; 레이아웃·크기 문제는 `QVBoxLayout` 등 레이아웃 위젯으로 해결.
- **Atomic 과용 금지**: 사소한 위젯까지 클래스만 늘리지 말 것(실용 우선).

상세: `@anivault-qt-gui`, `documents/QT_Architecture_Spec.md`.

---

## 문서

- `protocols/`, `persona/` — 패르소나 형식
- `documents/QT_Architecture_Spec.md` — Qt GUI 상세

---

## Cursor 활용 팁

Cursor를 100%에 가깝게 쓰기 위한 요약. 상세는 `@.cursor/rules/anivault-cursor-usage.mdc`.

- **계획 먼저**: 복잡한 작업은 Plan 모드 또는 "플랜만 작성해줘"도 쓸 수 있으나, **최종 계획은 리포지토리 MD에 남기고** 그 문서를 사람이 승인한 뒤 구현한다(위 **기획과 코딩의 분리**).
- **세션 분리**: 새 주제·새 작업이면 새 채팅으로 분리하고, 채팅당 목표 1개를 유지.
- **참조 최소화**: "전체 파일" 대신 파일+줄/함수/심볼로 범위를 좁혀 지시하고, 장문 로그·전문 붙여넣기를 줄인다.
- **작업 방식 분리**: 간단한 요청은 한 메시지에 묶고, 복잡한 설계·디버깅은 단계로 나눠 정확도 우선.
- **모델/도구 선택**: 난이도에 맞게 모델·모드를 선택하고, 관련 작업에 필요한 MCP만 사용한다. (`@anivault-mcp`)
- **스스로 확인**: 구현 후 검증 방법 제공(pytest, ruff, mypy, black 및 필요 시 실행/브라우저).
- **Cursor 전용 메모**: `docs/CURSOR_MEMO.md`에 실수 목록·규칙·다음 할 일 유지; 실수 시 "메모 업데이트해줘" 지시.
- **맥락 유지**: 중요한 결정·진행 상황은 파일로 저장하고, 새 세션 시 해당 파일 @로 전달.
- **설계서 먼저**: 코드 작성 전에 protocols/documents에 스펙·설계 정리 후 "이 설계대로 구현해줘" 지시.
- **Agent Skills·Taste Skill**: Cursor는 `SKILL.md` **Agent Skills**를 공식 지원; Taste Skill 등은 **서드파티**이며 웹 전제가 많다. **GUI 작업용 문서는** 리포의 `.mdc` **Rule**([anivault-agent-skills-taste-qt.mdc](.cursor/rules/anivault-agent-skills-taste-qt.mdc))로 원칙만 차용·PySide6/Qt로 번역(Skill 파일과 혼동 금지).

---

## MCP 활용 (적극 권장)

**활성화된 MCP 서버를 적극 활용한다.** 관련 작업 시 우선 MCP 도구를 사용할지 판단.

| 서버 | 용도 | 활용 시점 |
|------|------|-----------|
| **user-context7** | 라이브러리·프레임워크 최신 문서·코드 예제 조회 | 라이브러리 사용법, API 참조, 설정 질문, 코드 생성 시 |
| **GitLens** | Git 히스토리·브랜치·커밋 정보 | 변경 이력 추적, 코드 리뷰 준비, 브랜치 분석 시 |
| **cursor-ide-browser** | 웹 탐색·브라우저 자동화·캔버스 | 프론트엔드 테스트, 라이브 문서 확인, 인터랙티브 시각화 시 |

**DO**
- 신규 라이브러리·API 도입 전: context7로 최신 문서·예제 확인
- 웹 기반 문서 검증·테스트 필요 시: browser 도구 활용
- `call_mcp_tool`, `fetch_mcp_resource` 호출 전 스키마 확인 (`mcps/<server>/tools/`)

---

## 보안·커밋

- API 키: `.env`, 코드 하드코딩 금지
- 커밋: `[모듈] 요약`, 검증 4단계 통과 후
