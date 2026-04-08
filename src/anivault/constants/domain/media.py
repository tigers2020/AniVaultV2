"""Domain constants for media classification and scanning."""

from __future__ import annotations

from typing import Final

MEDIA_KIND_VIDEO: Final[str] = "video"
MEDIA_KIND_SUBTITLE: Final[str] = "subtitle"
MEDIA_KIND_OTHER: Final[str] = "other"

VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".mkv",
        ".mp4",
        ".avi",
        ".webm",
        ".ts",
        ".m2ts",
    }
)

SUBTITLE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".srt",
        ".ass",
        ".ssa",
        ".vtt",
        ".smi",
        ".sub",
    }
)

IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset()

VIDEO_SCAN_EXTENSIONS: Final[tuple[str, ...]] = tuple(sorted(VIDEO_EXTENSIONS))
SUBTITLE_SCAN_EXTENSIONS: Final[tuple[str, ...]] = tuple(sorted(SUBTITLE_EXTENSIONS))
