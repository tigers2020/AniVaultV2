# AniVault V2

애니메이션 라이브러리 **스캔·매칭·정리** 도구. V2는 그린필드 전략으로 재구성한다.

- **문서 인덱스**: [documents/README.md](documents/README.md)
- **아키텍처·GUI**: [documents/QT_Architecture_Spec.md](documents/QT_Architecture_Spec.md)
- **프로토콜**: [protocols/README.md](protocols/README.md)
- **페르소나**: [persona/README.md](persona/README.md)

## 요구 사항

- **Python 3.12+**

## 설치

```bash
pip install -e .
```

## TMDB / `.env`

- `env.example`를 참고해 프로젝트 루트에 `.env`를 두고 `TMDB_API_KEY=` 를 설정한다.
- 다른 경로를 쓰려면 환경 변수 `ANIVAULT_DOTENV_PATH`에 `.env` 파일 절대 경로를 지정한다.
- 설정 화면의 **TMDB API key**는 동일한 값을 읽고 `.env`에 저장한다 (`config.json`에는 넣지 않음).

## 구조

```
src/anivault/
  __main__.py   # python -m anivault → GUI
  domain/       # 모델, 서비스, 규칙
  application/  # 유스케이스, DTO, ports(계약)
  adapters/     # fs, metadata/tmdb, cache, operation_log
  interfaces/   # gui/main.py (비즈니스 로직 없음)
  bootstrap/    # container, settings
tests/
  unit/
  integration/
  golden/       # 파일명 코퍼스, 정규화 샘플
```

- **ports**: `application/ports` — MetadataProvider, FileRepository, OperationLogRepository, CacheRepository. 어댑터가 구현.
- **진입점**: GUI `interfaces/gui/main.py`. `python -m anivault`로 실행.

## 테스트

```bash
pytest
```

## V1 동결 (Phase 0)

`v1-freeze` 이후 V1에는 신규 기능을 넣지 않으며, 치명적 버그만 수정한다.  
일반 개선·리팩토링·신규 기능은 V2에서만 진행한다.
