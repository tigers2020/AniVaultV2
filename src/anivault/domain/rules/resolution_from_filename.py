"""resolution_from_filename.py

미디어 파일 경로·베이스명에서 표시용 해상도(Np, 4K, WxH)를 추출·정규화한다.

Author: Pom Kim
"""

from __future__ import annotations

import re
from pathlib import Path

_WxH = re.compile(r"\b(\d{3,4})\s*[x×]\s*(\d{3,4})\b", re.IGNORECASE)
_SHORT = re.compile(
    r"\b(2160p|1080p|720p|576p|480p|360p|4k)\b",
    re.IGNORECASE,
)


def normalize_resolution_from_raw(raw: str) -> str:
    """anitopy 스타일 또는 단순 해상도 문자열을 짧은 라벨로 맞춘다.

    Args:
        raw: 원본 해상도 문자열.

    Returns:
        예: 1280x720 → 720p. 빈 입력이면 빈 문자열.
    """
    if not raw or not raw.strip():
        return ""
    s = raw.strip()
    m = _SHORT.search(s)
    if m:
        return m.group(1).lower()
    m = re.search(r"(?:x|×)\s*(\d+)|^\s*(\d+)\s*$", s)
    if m:
        h = int(m.group(1) or m.group(2) or "0")
        return _height_to_label(h) or s
    return s


def _height_to_label(h: int) -> str:
    """세로 픽셀 높이를 짧은 p 라벨로 변환한다.

    Args:
        h: 세로(또는 기준) 픽셀 수.

    Returns:
        2160p 등. 구간에 없으면 빈 문자열.
    """
    if h >= 2160:
        return "2160p"
    if h >= 1080:
        return "1080p"
    if h >= 720:
        return "720p"
    if h >= 576:
        return "576p"
    if h >= 480:
        return "480p"
    if h >= 360:
        return "360p"
    return ""


def _video_height(w: int, h: int) -> int:
    """가로×세로에서 영상 높이로 쓸 값을 고른다(가로가 긴 전제).

    Args:
        w: 가로 픽셀.
        h: 세로 픽셀.

    Returns:
        세로가 더 작거나 같으면 min, 아니면 max.
    """
    return min(w, h) if w >= h else max(w, h)


def _best_dimension_label(stem: str) -> str:
    """stem에서 WxH 후보 중 가장 큰 영상 높이에 해당하는 라벨을 고른다.

    Args:
        stem: 파일명 stem(확장자 제외).

    Returns:
        720p 등 또는 WxH 문자열. 없으면 빈 문자열.
    """
    best_h = 0
    best_pair: tuple[int, int] | None = None
    for m in _WxH.finditer(stem):
        w, h = int(m.group(1)), int(m.group(2))
        vh = _video_height(w, h)
        if vh > best_h:
            best_h = vh
            best_pair = (w, h)
    if not best_pair:
        return ""
    label = _height_to_label(best_h)
    if label:
        return label
    bw, bh = best_pair
    return f"{bw}x{bh}"


def resolution_label_from_stream_dimensions(width: int, height: int) -> str:
    """비디오 스트림 너비·높이에서 표시용 해상도 라벨을 만든다.

    Args:
        width: 스트림 가로 픽셀.
        height: 스트림 세로 픽셀.

    Returns:
        720p/1080p 같은 라벨 또는 ``WxH``. 입력이 유효하지 않으면 빈 문자열.
    """
    if width <= 0 or height <= 0:
        return ""
    video_height = _video_height(width, height)
    label = _height_to_label(video_height)
    if label:
        return label
    return f"{width}x{height}"


def resolution_from_filename(filename: str) -> str:
    """전체 경로 또는 베이스명에서 짧은 해상도 라벨을 반환한다.

    Args:
        filename: 파일 경로 또는 이름.

    Returns:
        Np/4K/WxH 기반 짧은 라벨. 없으면 빈 문자열.
    """
    try:
        stem = Path(filename).stem
    except Exception:
        stem = filename
    m = _SHORT.search(stem)
    if m:
        return m.group(1).lower()
    return _best_dimension_label(stem)
