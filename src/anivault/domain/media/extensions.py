"""extensions.py

비디오·자막 확장자 집합과 media_kind 분류. 스캔·인덱스·동반자막이 동일 출처만 사용한다.

Author: Pom Kim
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

MediaKind = Literal["video", "subtitle", "other"]

# 점 포함 소문자. scan_library / FileRepository 와 동일 집합.
VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mkv",
        ".mp4",
        ".avi",
        ".webm",
        ".ts",
        ".m2ts",
    }
)

# companion_subtitles 와 동일 멤버.
SUBTITLE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".srt",
        ".ass",
        ".ssa",
        ".vtt",
        ".smi",
        ".sub",
    }
)

# 포스터 등 Phase 1 이후 확장용 자리.
IMAGE_EXTENSIONS: frozenset[str] = frozenset()

VIDEO_SCAN_EXTENSIONS: tuple[str, ...] = tuple(sorted(VIDEO_EXTENSIONS))
SUBTITLE_SCAN_EXTENSIONS: tuple[str, ...] = tuple(sorted(SUBTITLE_EXTENSIONS))


def classify_media_kind(path: str | Path) -> MediaKind:
    """경로 확장자로 미디어 종류를 분류한다.

    Args:
        path: 파일 경로.

    Returns:
        `video`, `subtitle`, 또는 `other`.
    """
    suf = Path(path).suffix.lower()
    if suf in VIDEO_EXTENSIONS:
        return "video"
    if suf in SUBTITLE_EXTENSIONS:
        return "subtitle"
    if suf in IMAGE_EXTENSIONS:
        return "other"
    return "other"
