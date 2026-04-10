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
    """stem에서 시즌 번호 문자열을 추출한다.

    ``S02``/``Season 3``/``1st``/``16th`` 등은 시즌으로 본다.
    ``N화``는 회차(에피소드)이므로 시즌으로 쓰지 않는다.

    ``S01E05``처럼 붙은 형태는 :func:`_extract_season_episode`에서 처리한다.
    단독 ``S##``는 여기서 ``\\bS(\\d+)\\b``로 잡는다(``S01E05``의 ``S01``은 경계 때문에 미매칭).

    Args:
        stem: 파일명 stem.

    Returns:
        시즌 숫자 문자열. 없으면 빈 문자열.
    """
    m = re.search(r"(?:season\s*(\d+)|\bS(\d+)\b)", stem, re.I)
    if m:
        g = (m.group(1) or m.group(2) or "").strip()
        if g.isdigit():
            return str(int(g))
        return g
    m = re.search(r"\b(\d+)(?:st|nd|rd|th)\b", stem, re.I)
    if m:
        return str(int(m.group(1)))
    return ""


def _extract_season_episode(stem: str) -> tuple[str, str]:
    """stem에서 시즌·에피소드를 추출한다.

    최우선 ``S##E##``(사이에 공백·``.``·``-``·``_`` 허용). 없으면 기존 시즌 규칙과
    단독 ``EP##`` / ``E##`` 에피 패턴을 쓴다.

    Args:
        stem: 파일명 stem.

    Returns:
        ``(season, episode)``. 없으면 해당 항목은 빈 문자열.
    """
    m_se = re.search(r"(?i)S(\d+)[\s.\-_]*E(\d+)", stem)
    if m_se:
        return str(int(m_se.group(1))), str(int(m_se.group(2)))
    m_dash = re.search(r"(?i)\bS(\d+)\b\s*-\s*(\d+)\b", stem)
    if m_dash:
        return str(int(m_dash.group(1))), str(int(m_dash.group(2)))
    season = _extract_season(stem)
    episode = ""
    m_ep = re.search(r"(?i)\bEP(\d+)\b", stem)
    if m_ep:
        episode = str(int(m_ep.group(1)))
    else:
        m_e = re.search(r"(?i)\bE(\d+)\b", stem)
        if m_e:
            episode = str(int(m_e.group(1)))
    return season, episode


def _normalize_episode_numbers(values: list[int]) -> list[int]:
    """Preserve order while removing duplicates and non-positive numbers."""
    out: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value <= 0 or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _episode_numbers_from_text(raw: str) -> list[int]:
    """Parse a single episode token or range token into normalized episode numbers."""
    text = (raw or "").strip()
    if not text:
        return []
    range_match = re.fullmatch(r"(\d+)\s*[-~]\s*(\d+)", text)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        if start <= end:
            return list(range(start, end + 1))
        return [start, end]
    if text.isdigit():
        return [int(text)]
    return [int(match) for match in re.findall(r"\d+", text)]


def _episode_numbers_to_text(values: list[int]) -> str:
    """Render normalized episode numbers to a compact display string."""
    numbers = _normalize_episode_numbers(values)
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    if numbers == list(range(numbers[0], numbers[-1] + 1)):
        return f"{numbers[0]}-{numbers[-1]}"
    return ",".join(str(value) for value in numbers)


def _extract_episode_numbers(stem: str) -> list[int]:
    """Extract episode numbers from common filename patterns."""
    m_se = re.search(r"(?i)S(\d+)[\s.\-_]*E(\d+(?:\s*[-~]\s*\d+)?)", stem)
    if m_se:
        return _episode_numbers_from_text(m_se.group(2))
    m_dash = re.search(r"(?i)\bS(\d+)\b\s*-\s*(\d+(?:\s*[-~]\s*\d+)?)\b", stem)
    if m_dash:
        return _episode_numbers_from_text(m_dash.group(2))
    m_ep = re.search(r"(?i)\bEP(\d+(?:\s*[-~]\s*\d+)?)\b", stem)
    if m_ep:
        return _episode_numbers_from_text(m_ep.group(1))
    m_e = re.search(r"(?i)\bE(\d+(?:\s*[-~]\s*\d+)?)\b", stem)
    if m_e:
        return _episode_numbers_from_text(m_e.group(1))
    m_plain_dash = re.search(
        r"(?i)(?:^|[\s._\]])-+[\s._]*(\d+(?:(?:\s*[-~,]\s*)\d+)+)\b",
        stem,
    )
    if m_plain_dash:
        return _episode_numbers_from_text(m_plain_dash.group(1))
    return []


def _episode_from_anitopy(value: object) -> str:
    """anitopy ``episode_number`` 등을 표시용 에피 문자열로 만든다."""
    s = _anitopy_field_str(value)
    if not s:
        return ""
    numbers = _episode_numbers_from_anitopy(value)
    if numbers:
        return _episode_numbers_to_text(numbers)
    if s.isdigit():
        return str(int(s))
    return s.strip()


def _episode_numbers_from_anitopy(value: object) -> list[int]:
    """Extract normalized episode numbers from anitopy episode fields."""
    if value is None:
        return []
    if isinstance(value, list):
        numbers: list[int] = []
        for item in value:
            numbers.extend(_episode_numbers_from_anitopy(item))
        return _normalize_episode_numbers(numbers)
    return _normalize_episode_numbers(_episode_numbers_from_text(str(value).strip()))


def _extract_year(stem: str) -> str:
    """stem에서 4자리 연도를 찾는다.

    Args:
        stem: 파일명 stem.

    Returns:
        연도 문자열. 없으면 빈 문자열.
    """
    m = re.search(r"\b(19\d{2}|20\d{2})\b", stem)
    return m.group(1) if m else ""


def _anitopy_field_str(value: object) -> str:
    """anitopy 필드값을 단일 문자열로 정규화한다.

    anitopy는 ``video_resolution`` 등 일부 키에 list를 넣는 경우가 있어
    ``str.strip()`` 호출 전에 처리한다.

    Args:
        value: anitopy가 반환한 임의 값.

    Returns:
        공백 정리된 문자열. None·빈 값이면 빈 문자열.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        parts = [_anitopy_field_str(v) for v in value]
        return " ".join(p for p in parts if p).strip()
    return str(value).strip()


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
        season, episode = _extract_season_episode(stem)
        episode_numbers = _extract_episode_numbers(stem)
        episode = episode or _episode_numbers_to_text(episode_numbers)
        return ParsedInfo(
            title=title,
            parse_group=title,
            year=_extract_year(stem),
            season=season,
            episode=episode,
            episode_numbers=episode_numbers,
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
        title_raw = _anitopy_field_str(data.get("anime_title")) if data else ""
        if not title_raw:
            return self._fallback.parse(filename)
        title = title_raw
        year = _anitopy_field_str(data.get("anime_year")) if data else ""
        year = year or _extract_year(stem)
        stem_season, stem_episode = _extract_season_episode(stem)
        stem_episode_numbers = _extract_episode_numbers(stem)
        anitopy_episode = _episode_from_anitopy(data.get("episode_number")) if data else ""
        anitopy_episode_numbers = (
            _episode_numbers_from_anitopy(data.get("episode_number")) if data else []
        )
        episode_numbers = stem_episode_numbers or anitopy_episode_numbers
        season = stem_season
        episode = stem_episode or _episode_numbers_to_text(episode_numbers) or anitopy_episode
        res_raw = _anitopy_field_str(data.get("video_resolution")) if data else ""
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
            episode=episode,
            episode_numbers=episode_numbers,
            resolution=resolution,
        )
