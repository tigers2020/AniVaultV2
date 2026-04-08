"""extensions.py

Video/subtitle extension sets and media-kind classification helpers.

Author: Pom Kim
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from anivault.constants.domain.media import (
    IMAGE_EXTENSIONS,
    MEDIA_KIND_OTHER,
    MEDIA_KIND_SUBTITLE,
    MEDIA_KIND_VIDEO,
    SUBTITLE_EXTENSIONS,
    SUBTITLE_SCAN_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VIDEO_SCAN_EXTENSIONS,
)

MediaKind = Literal["video", "subtitle", "other"]

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
        return cast(MediaKind, MEDIA_KIND_VIDEO)
    if suf in SUBTITLE_EXTENSIONS:
        return cast(MediaKind, MEDIA_KIND_SUBTITLE)
    if suf in IMAGE_EXTENSIONS:
        return cast(MediaKind, MEDIA_KIND_OTHER)
    return cast(MediaKind, MEDIA_KIND_OTHER)
