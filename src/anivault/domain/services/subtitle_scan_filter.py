"""subtitle_scan_filter.py

스캔 목록에서 동일 폴더·동일 stem 비디오가 있는 자막 경로를 제외한다.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from anivault.constants.domain.media import MEDIA_KIND_SUBTITLE, VIDEO_EXTENSIONS
from anivault.domain.media.extensions import classify_media_kind


def _video_stems_in_directory(parent: Path) -> set[str]:
    """Return file stems of regular files whose suffix is a known video extension."""
    stems: set[str] = set()
    try:
        for child in parent.iterdir():
            if not child.is_file():
                continue
            if child.suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            stems.add(child.stem)
    except OSError:
        pass
    return stems


def filter_subtitle_paths_without_paired_video(paths: Sequence[Path]) -> list[Path]:
    """같은 부모 폴더에 동일 stem 의 비디오가 있으면 해당 자막 경로를 빼고 순서를 유지한다.

    비디오 존재 여부는 부모별로 한 번씩 `iterdir`하여 `VIDEO_EXTENSIONS` 와 일치하는
    파일 stem을 모은 뒤 판단한다.

    Args:
        paths: 스캔된 경로(주로 자막 확장자만).

    Returns:
        `paths`의 부분열. 자막이 아닌 경로는 그대로 둔다.
    """
    if not paths:
        return []
    unique_parents = {p.parent for p in paths}
    video_stems_by_parent = {parent: _video_stems_in_directory(parent) for parent in unique_parents}

    out: list[Path] = []
    for p in paths:
        if classify_media_kind(p) != MEDIA_KIND_SUBTITLE:
            out.append(p)
            continue
        if p.stem in video_stems_by_parent.get(p.parent, set()):
            continue
        out.append(p)
    return out
