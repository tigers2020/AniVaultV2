# AGENTS.md

Cursor AI용 AniVault V2 프로젝트 가이드. [AGENTS.md](https://agents.md/) 표준.

> 핵심: `.cursor/rules/anivault-root.mdc`가 최상위 사전 지시서. 이 문서는 원칙과 운영 게이트만 짧게 잡고, 세부 절차는 `.cursor/rules/`와 `persona/`로 위임한다.

---

## 진행 방식: Persona Dialogue 3단계

모든 코딩·진행은 아래 3단계를 따른다. 자연스러운 구어체로 짧게 쓴다.

1. `[시몬]`이 요청을 요약하고 책임 소제를 나눈다.
2. 배정받은 담당자가 한두 문장으로 접근 방식을 브리핑한다.
3. 그 뒤에만 코드 작성·수정을 진행한다.

구현이 끝나면 `[테스]`가 테스트를 맡고, `[렉스]`가 `pytest → ruff check . → mypy src → black .` 순서로 검증한다.

레이어 빠른 매핑:

| 역할 | 담당 |
|------|------|
| 시몬 | 분배·조율·게이트 |
| 도미닉 | `domain/` |
| 유리 | `application/` |
| 아다 | `adapters/` |
| 지나 | `interfaces/gui/` |
| 테스 | `tests/` |
| 렉스 | 검증 파이프라인 |

상세 절차와 카드:

- `.cursor/rules/anivault-persona-dialogue.mdc`
- `persona/README.md`

---

## 기획과 코딩의 분리

원칙: 사람이 문서로 된 계획을 검토·승인하기 전까지 에이전트는 구현으로 넘어가지 않는다.

고정 게이트:

- 리서치: 관련 코드와 규칙을 읽고 `docs/` 또는 `documents/`에 조사 문서를 남긴다.
- 플랜: 변경 접근, 대상 경로, 트레이드오프를 담은 플랜 MD를 저장한다.
- 승인: 사람이 플랜 문서 본문에서 검토·수정·승인한다.
- 구현: 승인 후에만 코드 작성·수정으로 넘어간다.

시몬은 플랜이 닫히기 전까지 3단계 구현 진입을 허용하지 않는다.

---

## 프로젝트 개요

**AniVault V2** — 애니메이션 라이브러리 스캔·매칭·정리. GUI-only Qt.

워크플로우: **스캔** → **타이틀 클리닝** → **매칭** → **정리(plan→apply)** → (선택) 롤백

---

## 규칙 우선순위

1. `@.cursor/rules/anivault-root.mdc` — 자기 검증 4단계, 도메인 용어, DO/DON'T
2. `@.cursor/rules/anivault-architecture.mdc` — 레이어·포트
3. `@.cursor/rules/anivault-mcp.mdc` — MCP 활용
4. `@.cursor/rules/anivault-cursor-usage.mdc` — 계획 선행, 메모, 다중 채팅
5. `@.cursor/rules/anivault-persona-dialogue.mdc` — Persona Dialogue, 역할 핸드오프
6. `@.cursor/rules/anivault-qt-gui.mdc` 등 glob 규칙 — 파일/디렉터리별 적용

---

## 하네스 엔지니어링

- 프롬프트가 아니라 구조로 실수를 줄인다: 테스트, 린트, 레이어 규칙, 계획 승인 게이트.
- 컨텍스트 지도는 `AGENTS.md`, `.cursor/rules/`, `docs/CURSOR_MEMO.md`다.
- 재현된 실수는 테스트와 `docs/CURSOR_MEMO.md`에 남겨 반복을 줄인다.
- 외부 기업 사례·수치·인용은 검증 가능한 출처 없이 사실처럼 단정하지 않는다.

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

```text
src/anivault/
  domain/       application/   adapters/   interfaces/gui/   bootstrap/
  interfaces/gui/components/: atoms/ → molecules/ → organisms/
tests/  unit/  integration/  golden/
```

Qt GUI 상세는 `documents/QT_Architecture_Spec.md`, GUI 역할 카드는 `persona/gina-gui.md`를 본다.

---

## 완료 보고 원칙

- 변경 파일, 검증 명령, 미실행 사유를 짧게 보고한다.
- 검증 실패 시 실패한 명령, 이유, 다음 담당 캐릭터를 남긴다.
- `black .`이 파일을 바꿨으면 "검증 통과"와 별도로 "포맷 변경 발생"을 함께 보고한다.

검증을 못 돌렸다면 최소 아래 3가지를 남긴다.

- 실행 못 한 명령
- 이유
- 남은 위험

---

## 보안·커밋

- API 키: `.env`, 코드 하드코딩 금지
- 커밋: `[모듈] 요약`, 검증 4단계 통과 후
