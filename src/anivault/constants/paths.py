"""paths.py

AniVault 앱 데이터 디렉터리의 단일 진실 소스.

모든 퍼시스턴스·설정·로그 경로는 여기서 파생한다.
별도 오버라이드가 필요하면 환경 변수(ANIVAULT_DOTENV_PATH 등)를 사용하고,
이 상수들을 직접 교체하지 않는다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

APP_STATE_DIR: Final[Path] = Path.home() / ".anivault"
