"""__init__.py

미디어 확장자·종류 분류 단일 출처.

Author: Pom Kim
"""

from anivault.domain.media.extensions import (
    SUBTITLE_EXTENSIONS,
    SUBTITLE_SCAN_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VIDEO_SCAN_EXTENSIONS,
    MediaKind,
    classify_media_kind,
)

__all__ = [
    "SUBTITLE_EXTENSIONS",
    "SUBTITLE_SCAN_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "VIDEO_SCAN_EXTENSIONS",
    "MediaKind",
    "classify_media_kind",
]
