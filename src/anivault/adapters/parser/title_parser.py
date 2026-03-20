"""Filename parser: anitopy-first with regex fallback. Fills title, year, season, resolution."""

import re
from pathlib import Path

import anitopy  # type: ignore[import-untyped]

from anivault.application.dto.parse import ParsedInfo
from anivault.application.ports.filename_parser import FilenameParser
from anivault.domain.rules.resolution_from_filename import (
    normalize_resolution_from_raw,
    resolution_from_filename,
)


def _token_set(ignore_tokens: str) -> set[str]:
    return {t.strip().lower() for t in (ignore_tokens or "").split(",") if t.strip()}


def _clean_title(stem: str, tokens: set[str]) -> str:
    """Remove tokens and normalize separators; return non-empty title."""
    s = stem.replace(".", " ").replace("_", " ").replace("-", " ")
    parts = s.split()
    kept = [p for p in parts if p.lower() not in tokens and not p.isdigit()]
    return " ".join(kept).strip() if kept else stem


def _extract_season(stem: str) -> str:
    m = re.search(r"(?:season|s)\s*(\d+)|(\d+)\s*화", stem, re.I)
    if m:
        return m.group(1) or m.group(2) or ""
    return ""


def _extract_year(stem: str) -> str:
    m = re.search(r"\b(19\d{2}|20\d{2})\b", stem)
    return m.group(1) if m else ""


def _get_stem(filename: str) -> str:
    try:
        return Path(filename).stem
    except Exception:
        return filename


class MinimalTitleParser(FilenameParser):
    """Fallback parser: regex-only. ignore_tokens for title cleaning."""

    def __init__(self, ignore_tokens: str = "") -> None:
        self._tokens = _token_set(ignore_tokens)

    def parse(self, filename: str) -> ParsedInfo:
        """예외 없이 ParsedInfo 반환. 실패 시 title=stem."""
        stem = _get_stem(filename)
        title = _clean_title(stem, self._tokens) or stem
        return ParsedInfo(
            title=title,
            parse_group=title,
            year=_extract_year(stem),
            season=_extract_season(stem),
            resolution=resolution_from_filename(filename),
        )


class AnitopyTitleParser(FilenameParser):
    """anitopy 1차, 실패/빈 결과 시 MinimalTitleParser fallback. 테이블용 title/year/season/resolution 채움."""

    def __init__(self, ignore_tokens: str = "") -> None:
        self._fallback = MinimalTitleParser(ignore_tokens=ignore_tokens)

    def parse(self, filename: str) -> ParsedInfo:
        """예외 없이 ParsedInfo 반환. anitopy 성공 시 매핑, 실패 시 fallback."""
        stem = _get_stem(filename)
        try:
            data = anitopy.parse(stem)
        except Exception:
            return self._fallback.parse(filename)
        title_raw = (data.get("anime_title") or "").strip()
        if not title_raw:
            return self._fallback.parse(filename)
        title = title_raw
        year = (data.get("anime_year") or "").strip() or _extract_year(stem)
        season = _extract_season(stem)  # anitopy has no season field
        res_raw = (data.get("video_resolution") or "").strip()
        resolution = (
            normalize_resolution_from_raw(res_raw)
            if res_raw
            else resolution_from_filename(filename)
        )
        return ParsedInfo(
            title=title,
            parse_group=title,
            year=year,
            season=season,
            resolution=resolution,
        )
