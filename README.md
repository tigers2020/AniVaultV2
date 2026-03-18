# AniVault V2

애니메이션 라이브러리 **스캔·매칭·정리** 도구. V2는 그린필드 전략으로 재구성한다.

- **아키텍처·Phase**: [documents/QT_Architecture_Spec.md](documents/QT_Architecture_Spec.md)
- **프로토콜**: [protocols/](protocols/)

## 요구 사항

- **Python 3.12+**

## 설치

```bash
pip install -e .
```

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
