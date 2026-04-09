# Cursor 전용 메모

Cursor(Composer/Agent) 작업 시 팀 규칙·진행 맥락·반복 실수 목록을 모아두는 파일. 새 세션 시작 시 `@docs/CURSOR_MEMO.md`로 맥락 전달. 실수 발생 시 "이 메모 업데이트해줘, 같은 실수 반복하지 마" 지시.

---

## 팀/프로젝트 규칙 요약

- 상세: `@AGENTS.md`, `@.cursor/rules/anivault-root.mdc`
- **진입점**: `python -m anivault` → GUI(README 동일). 외부 메모·스킬이 “CLI 우선”이라고 해도 이 리포 기준과 혼동하지 말 것.
- **GUI 규칙**: GUI 작업은 `@persona/gina-gui.md`와 `@.cursor/rules/anivault-qt-gui.mdc`를 함께 본다.
- 진행: 3단계 대화형(시몬 브리핑 → 담당 브리핑 → 코딩) → 테스 테스트 → 렉스 검증
- 계획 게이트: 리서치 문서 → 플랜 MD → 사람 승인 → 구현
- 문서 위치: 기본은 `docs/`, 필요 시 `documents/`
- 검증: `pytest` → `ruff check .` → `mypy src` → `black .`
- 미실행 보고: 실행 못 한 명령 / 이유 / 남은 위험
- `black .`이 파일을 바꾸면 포맷 변경 발생도 함께 보고

---

## 반복 실수 목록

(실수 발생 시 AI에게 "이 메모의 반복 실수 목록에 추가하고 같은 실수 다시 하지 마"라고 지시.)

- (비어 있음 — 운영하면서 추가)

---

## 현재 맥락

- **지금 어디까지 왔는지**: (작성 시 업데이트)
- **다음에 할 작업**: (작성 시 업데이트)
