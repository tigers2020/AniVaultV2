# AGENTS.md

Cursor AI용 AniVault V2 프로젝트 가이드. [AGENTS.md](https://agents.md/) 표준.

> **핵심**: `.cursor/rules/anivault-root.mdc`가 사전 지시서. 자기 검증·도메인 용어·@참조. 200줄 이하.

---

## 진행 방식: 캐릭터 대화형 (Persona Dialogue)

**모든 코딩·진행은 `persona/` 캐릭터들의 대화 형식. 자연스러운 구어체로.**

### 대화 규칙

- **자연체**: 격식 있는 문어가 아니라, 팀원끼리 대화하듯 자연스러운 말투.
- 시몬이 흐름을 잡고, 캐릭터들이 서로 말걸고 요청하고 답하고.
- `[시몬]` `[도미닉]` 등으로 누가 말하는지만 구분.

### 예시 (자연스러운 대화)

```
[시몬] 매칭 스코어 넣으라는 요청 들어왔어. confidence 계산이 필요한데, 도미닉 이거 네 담당이지?

[도미닉] 응, domain/rules/에 ConfidenceThresholds 만들게. HIGH 0.8, MEDIUM 0.5, LOW 0.2로 둘까?

[유리] 그럼 난 MatchUseCase에서 거기 호출하면 되겠네. 포트만 쓰고, TMDB 쪽 변환은 아다가 하잖아.

[아다] 맞아, 우리는 응답 → DTO만. 스코어링은 안 건드릴게.

[시몬] ㅇㅋ. 도미닉부터 하고 → 유리 → 아다 순으로 가자. 다 끝나면 pytest, ruff, mypy, black 돌려보고 알려줘.
```

---

## 프로젝트 개요

**AniVault V2** — 애니메이션 라이브러리 스캔·매칭·정리. GUI-only Qt.

워크플로우: **스캔** → **타이틀 클리닝** → **매칭** → **정리(plan→apply)** → (선택) 롤백

---

## 규칙 우선순위

1. **@.cursor/rules/anivault-root.mdc** — 자기 검증 4단계, 도메인 용어, DO/DON'T
2. **@.cursor/rules/anivault-architecture.mdc** — 레이어·포트
3. **@.cursor/rules/anivault-qt-gui.mdc** 등 glob 규칙 — 파일/디렉터리별 적용

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
tests/  unit/  integration/  golden/
```

---

## 문서

- `protocols/`, `persona/` — 패르소나 형식
- `documents/QT_Architecture_Spec.md` — Qt GUI 상세

---

## 보안·커밋

- API 키: `.env`, 코드 하드코딩 금지
- 커밋: `[모듈] 요약`, 검증 4단계 통과 후
