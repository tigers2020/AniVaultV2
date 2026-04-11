# PySide6 / Qt 6 layout·구조 체크리스트 (Context7 대응)

이 문서는 GUI 표준화 플랜의 **선택** 후속으로, Upstash **Context7** MCP로 `resolve-library-id` → `query-docs`를 호출해 PySide6 문서를 당겨올 때 같은 축으로 검증하면 된다.

**환경 메모 (2026-04-10):** 이 워크스페이스 Cursor 세션에서는 `context7` MCP 서버가 등록되어 있지 않아 라이브 조회는 수행하지 못했다. 아래 항목은 Qt 6 / PySide6 공식 가이드 방향과 AniVault 규칙(`.cursor/rules/anivault-qt-gui.mdc`)을 기준으로 정리했다. 나중에 Context7을 켠 뒤 동일 키워드로 `query-docs`를 돌리면 버전별 문구를 보강할 수 있다.

## 권장 질의 토픽 (Context7)

| 주제 | 예시 `libraryName` / `query` |
|------|------------------------------|
| High DPI | PySide6, "high DPI scaling device pixel ratio" |
| QSplitter | PySide6, "QSplitter setSizes stretch collapsible" |
| QScrollArea | PySide6, "QScrollArea setWidgetResizable size policy" |
| QSizePolicy | PySide6, "QSizePolicy expanding preferred layout" |

## 체크리스트

### High DPI·디바이스 픽셀

- [ ] `QApplication` / `QGuiApplication` 초기화 시점에 DPI 관련 속성이 의도와 맞는지 확인한다 (Qt 6에서는 이전 Qt 5의 `AA_EnableHighDpiScaling` 등 일부 플래그가 제거·기본 동작 변경됨).
- [ ] `devicePixelRatio()`를 쓰는 커스텀 그리기·픽스맵 스케일이 있다면 논리 픽셀과 물리 픽셀을 구분한다.
- [ ] 고정 픽셀 상수는 **레이아웃 토큰 + 밀도 스케일**로 흡수하는 편이 안전하다 (`theme.py` / `responsive.py` 패턴).

### QSplitter

- [ ] `setChildrenCollapsible(False)`로 빈 패널 붕괴를 막을지 여부를 의도에 맞게 설정한다 (AniVault `ContentView` 등에서 사용).
- [ ] 초기 `setSizes`는 최소 너비·`sizeHint`와 함께 검토한다.
- [ ] 사용자가 조절한 스플리터 상태를 저장할 경우 복원 시 최소 크기 위반을 피한다.

### QScrollArea

- [ ] 스크롤 내부 콘텐츠 위젯에 `setWidgetResizable(True)`가 필요한지 명시한다.
- [ ] 스크롤바 정책(`ScrollBarAlwaysOff` 등)이 레이아웃 깨짐을 유발하지 않는지 확인한다.
- [ ] QSS로 크기를 억지로 잡지 말고, 규칙대로 **레이아웃·sizePolicy**로 잡는다.

### 레이아웃·QSS 경계

- [ ] 여백·간격은 `QLayout` + 공유 토큰(`theme.*_px()`) 우선.
- [ ] QSS는 색·테두리·상태 위주.

### AniVault 교차 참조

- [ ] [documents/docs/02-architecture/06-qt-architecture-spec.md](../02-architecture/06-qt-architecture-spec.md) — 페이지·프레젠터·컴포넌트 경계.
- [ ] `docs/gui-layout-standardization-plan.md` — 토큰 롤아웃 대상 위젯 목록.
