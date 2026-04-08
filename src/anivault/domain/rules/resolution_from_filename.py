"""Extract and normalize video resolution labels from filenames."""

from __future__ import annotations

import re
from pathlib import Path

_LABEL_8K_UHD = "8K UHD"

_WxH = re.compile(r"\b(\d{3,4})\s*[xX]\s*(\d{3,4})\b")
_HEIGHT_SUFFIX = re.compile(r"^\s*[xX]\s*(\d+)\s*$")
_WIDTH_TOKEN = re.compile(r"(?<![A-Za-z0-9])(1280|1920|2560|3840|7680)(?![A-Za-z0-9])")
_SHORT = re.compile(
    r"\b(4320p|2160p|1440p|1080p|720p|576p|480p|360p|8k|4k|2k)\b",
    re.IGNORECASE,
)
_SHORT_LABELS = {
    "360p": "SD",
    "480p": "SD",
    "576p": "SD",
    "720p": "HD",
    "1080p": "FHD",
    "1440p": "QHD",
    "2160p": "UHD",
    "4320p": _LABEL_8K_UHD,
    "2k": "QHD",
    "4k": "UHD",
    "8k": _LABEL_8K_UHD,
}
_WIDTH_LABELS = {
    "1280": "HD",
    "1920": "FHD",
    "2560": "QHD",
    "3840": "UHD",
    "7680": _LABEL_8K_UHD,
}
_LABEL_RANKS = {"HD": 0, "FHD": 1, "QHD": 2, "UHD": 3, _LABEL_8K_UHD: 4}


def normalize_resolution_from_raw(raw: str) -> str:
    """Normalize anitopy/raw resolution strings to standard tier labels.

    Args:
        raw: Original resolution text.

    Returns:
        Standard tier label, original text when unrecognized, or an empty string.
    """
    if not raw or not raw.strip():
        return ""
    s = raw.strip()
    m = _SHORT.search(s)
    if m:
        return _SHORT_LABELS[m.group(1).lower()]
    m = _WxH.search(s)
    if m:
        h = _video_height(int(m.group(1)), int(m.group(2)))
        return _height_to_label(h) or s
    m = _HEIGHT_SUFFIX.search(s)
    if m:
        h = int(m.group(1) or "0")
        return _height_to_label(h) or s
    m = _WIDTH_TOKEN.search(s)
    if m:
        return _WIDTH_LABELS[m.group(1)]
    m = re.search(r"^\s*(\d+)\s*$", s)
    if m:
        h = int(m.group(1) or "0")
        return _height_to_label(h) or s
    return s


def _height_to_label(h: int) -> str:
    """Round a video height up to the nearest standard resolution tier."""
    if h <= 0:
        return ""
    if h <= 480:
        return "SD"
    if h <= 720:
        return "HD"
    if h <= 1080:
        return "FHD"
    if h <= 1440:
        return "QHD"
    if h <= 2160:
        return "UHD"
    return _LABEL_8K_UHD


def _video_height(w: int, h: int) -> int:
    """Choose the video height from a WxH pair, allowing rotated dimensions."""
    return min(w, h) if w >= h else max(w, h)


def _best_dimension_label(text: str) -> str:
    """Return the best standard tier label from WxH tokens in text."""
    best_h = 0
    for m in _WxH.finditer(text):
        w, h = int(m.group(1)), int(m.group(2))
        vh = _video_height(w, h)
        if vh > best_h:
            best_h = vh
    return _height_to_label(best_h) if best_h else ""


def _width_token_label(text: str) -> str:
    """Return the best tier label from common standalone width tokens."""
    best_rank = -1
    best_label = ""
    for m in _WIDTH_TOKEN.finditer(text):
        label = _WIDTH_LABELS[m.group(1)]
        rank = _LABEL_RANKS[label]
        if rank > best_rank:
            best_rank = rank
            best_label = label
    return best_label


def _resolution_label_from_text(text: str) -> str:
    """Extract a standard tier from resolution-like tokens in text."""
    m = _SHORT.search(text)
    if m:
        return _SHORT_LABELS[m.group(1).lower()]
    label = _best_dimension_label(text)
    if label:
        return label
    return _width_token_label(text)


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
    """Extract a normalized standard resolution tier from a path or filename."""
    try:
        stem = Path(filename).stem
    except Exception:
        stem = filename
    return _resolution_label_from_text(stem) or _resolution_label_from_text(filename)
