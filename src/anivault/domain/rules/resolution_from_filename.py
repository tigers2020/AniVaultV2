"""Extract display resolution from a media file path or basename (Np, 4K, WxH)."""

from __future__ import annotations

import re
from pathlib import Path

_WxH = re.compile(r"\b(\d{3,4})\s*[x×]\s*(\d{3,4})\b", re.IGNORECASE)
_SHORT = re.compile(
    r"\b(2160p|1080p|720p|576p|480p|360p|4k)\b",
    re.IGNORECASE,
)


def normalize_resolution_from_raw(raw: str) -> str:
    """Map anitopy-style or bare resolution strings to short label (e.g. 1280x720 -> 720p)."""
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
    """Assume width x height with landscape releases; fallback to larger dimension."""
    return min(w, h) if w >= h else max(w, h)


def _best_dimension_label(stem: str) -> str:
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


def resolution_from_filename(filename: str) -> str:
    """Return short resolution label from a full path or basename (Np / 4K / WxH)."""
    try:
        stem = Path(filename).stem
    except Exception:
        stem = filename
    m = _SHORT.search(stem)
    if m:
        return m.group(1).lower()
    return _best_dimension_label(stem)
