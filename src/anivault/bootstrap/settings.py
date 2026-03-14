"""Application settings (paths, API keys, defaults)."""

from pathlib import Path

# 기본값; 환경 변수 또는 설정 파일로 오버라이드
DEFAULT_LOGS_DIR = Path(".anivault/logs")
SUPPORTED_VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov", ".webm")
