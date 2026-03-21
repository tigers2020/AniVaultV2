"""settings.py

애플리케이션 설정 상수(경로, 기본 확장자 등).

Author: Pom Kim
"""

from pathlib import Path

# 기본값; 환경 변수 또는 설정 파일로 오버라이드
DEFAULT_LOGS_DIR = Path(".anivault/logs")
SUPPORTED_VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".webm")
