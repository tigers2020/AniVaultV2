"""title_parser.py

FilenameParser 구현: anitopy 우선, 실패 시 정규식 폴백으로 제목·연도·시즌·해상도를 채운다.

Author: Pom Kim
"""

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
    """쉼표 구분 문자열을 소문자 토큰 집합으로 만든다.

    Args:
        ignore_tokens: 무시할 토큰 목록(쉼표 구분).

    Returns:
        공백 제거·소문자 토큰 집합.
    """
    return {t.strip().lower() for t in (ignore_tokens or "").split(",") if t.strip()}


def _clean_title(stem: str, tokens: set[str]) -> str:
    """stem에서 토큰·숫자 단어를 제거하고 구분자를 정규화한다.

    Args:
        stem: 파일명 stem.
        tokens: 제거할 소문자 토큰 집합.

    Returns:
        비어 있지 않으면 정리된 제목, 아니면 원본 stem.
    """
    s = stem.replace(".", " ").replace("_", " ").replace("-", " ")
    parts = s.split()
    kept = [p for p in parts if p.lower() not in tokens and not p.isdigit()]
    return " ".join(kept).strip() if kept else stem


def _extract_season(stem: str) -> str:
    """stem에서 시즌 또는 화 번호 문자열을 추출한다.

    Args:
        stem: 파일명 stem.

    Returns:
        시즌/화 숫자 문자열. 없으면 빈 문자열.
    """
    m = re.search(r"(?:season|s)\s*(\d+)|(\d+)\s*화", stem, re.I)
    if m:
        return m.group(1) or m.group(2) or ""
    return ""


def _extract_year(stem: str) -> str:
    """stem에서 4자리 연도를 찾는다.

    Args:
        stem: 파일명 stem.

    Returns:
        연도 문자열. 없으면 빈 문자열.
    """
    m = re.search(r"\b(19\d{2}|20\d{2})\b", stem)
    return m.group(1) if m else ""


def _get_stem(filename: str) -> str:
    """파일명에서 확장자를 뗀 stem을 반환한다.

    Args:
        filename: 파일명 또는 경로.

    Returns:
        Path.stem 또는 예외 시 원본 filename.
    """
    try:
        return Path(filename).stem
    except Exception:
        return filename


class MinimalTitleParser(FilenameParser):
    """정규식 전용 폴백 파서. ignore_tokens로 제목 정리."""

    def __init__(self, ignore_tokens: str = "") -> None:
        """토큰 집합을 준비한다.

        Args:
            self: 이 인스턴스.
            ignore_tokens: 제목에서 제거할 쉼표 구분 토큰.

        Returns:
            None.
        """
        self._tokens = _token_set(ignore_tokens)

    def parse(self, filename: str) -> ParsedInfo:
        """예외 없이 ParsedInfo를 반환한다. 실패 시 title은 stem.

        Args:
            self: 이 파서.
            filename: 파싱할 파일명.

        Returns:
            ParsedInfo.
        """
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
    """anitopy 1차, 빈 결과·예외 시 MinimalTitleParser로 폴백."""

    def __init__(self, ignore_tokens: str = "") -> None:
        """폴백 파서를 구성한다.

        Args:
            self: 이 인스턴스.
            ignore_tokens: 폴백 파서에 넘길 무시 토큰.

        Returns:
            None.
        """
        self._fallback = MinimalTitleParser(ignore_tokens=ignore_tokens)

    def parse(self, filename: str) -> ParsedInfo:
        """anitopy 성공 시 매핑하고, 실패 시 폴백을 쓴다.

        Args:
            self: 이 파서.
            filename: 파싱할 파일명.

        Returns:
            ParsedInfo. 항상 반환.
        """
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
