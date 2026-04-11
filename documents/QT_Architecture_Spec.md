# Qt GUI 아키텍처 (요약)

AniVault V2는 **PySide6 단일 프로세스 데스크톱 앱**이다. 비즈니스 규칙은 `domain/`, 유스케이스는 `application/`, I/O는 `adapters/`에 두고 GUI는 조립·표현에 집중한다.

## 진입

- `python -m anivault` → `anivault.interfaces.gui.main:run`
- `MainWindow` ([app.py](../src/anivault/interfaces/gui/app.py)): `AniVaultAppContainer`로 Organizer / 자막 Organizer / Settings 페이지 생성, `PipelineTableModel`로 파이프라인 상태 유지

## 레이어 (GUI 내부)

| 구역 | 역할 |
|------|------|
| `components/` | atoms → molecules → organisms 위젯 |
| `pages/` | 탭별 페이지 셸 |
| `presenters/` | 사용자 액션·워커·모델 갱신 (예: `OrganizerPresenter`, `ScanParseCoordinator`, `MatchCoordinator`) |
| `templates/` | 복합 패널 레이아웃 |
| `themes/`, `theme_runtime.py` | 스타일·밀도 |
| `i18n/` | 번역 키·로케일 |

Presenter는 유스케이스 실행 함수와 DTO만 알고, SQLite·TMDB 어댑터 구체는 **`bootstrap/container.py`** 에서 주입된다.

## 사용자 워크플로 (화면)

1. **Organizer**: 폴더 스캔 → 파싱 → TMDB 매칭 → Dry run / plan → apply  
2. **자막 Organizer**: 자막 확장자 위주 파이프라인  
3. **Settings**: 경로 규칙, TMDB 키(`.env`), 테마 등

상세 규칙은 `.cursor/rules/anivault-qt-gui.mdc`, 포트·유스케이스는 `.cursor/rules/anivault-architecture.mdc`를 본다.
