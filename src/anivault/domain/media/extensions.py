"""extensions.py

Video/subtitle extension sets and media-kind classification helpers.

Author: Pom Kim
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

from anivault.constants.domain.media import (
    IMAGE_EXTENSIONS,
    SUBTITLE_EXTENSIONS,
    SUBTITLE_SCAN_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VIDEO_SCAN_EXTENSIONS,
)

MediaKind = Literal["video", "subtitle", "other"]
VIDEO_MEDIA_KIND: Final[MediaKind] = "video"
SUBTITLE_MEDIA_KIND: Final[MediaKind] = "subtitle"
OTHER_MEDIA_KIND: Final[MediaKind] = "other"

__all__ = [
    "MediaKind",
    "VIDEO_EXTENSIONS",
    "SUBTITLE_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "VIDEO_SCAN_EXTENSIONS",
    "SUBTITLE_SCAN_EXTENSIONS",
    "classify_media_kind",
]


def classify_media_kind(path: str | Path) -> MediaKind:
    """Classify a path by suffix."""
    suf = Path(path).suffix.lower()
    if suf in VIDEO_EXTENSIONS:
        return VIDEO_MEDIA_KIND
    if suf in SUBTITLE_EXTENSIONS:
        return SUBTITLE_MEDIA_KIND
    if suf in IMAGE_EXTENSIONS:
        return OTHER_MEDIA_KIND
    return OTHER_MEDIA_KIND
