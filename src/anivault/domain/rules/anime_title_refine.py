"""anime_title_refine.py

파일명 파싱 직후 제목·그룹 키를 정리한다.

- ``N화``(한국어 화차)는 에피소드로 보고 제목에서 떼어 같은 시리즈로 묶는다.
- ``1st``/``2nd``/``16th`` 등 서수는 시즌 표기로 보고 제목에서는 제거한다(시즌은 stem에서 이미 추출).
- ``Nth TV YYYY`` + 릴즈 꼬리(DVDRip 등)는 DVD 팩 이름에서 제거한다.
- ``Durarara!!`` / ``x2 Ten|Ketsu|Shou`` 계열은 그룹 키를 ``Durarara!!``로 통일한다.

Author: Pom Kim
"""

from __future__ import annotations

import re

from anivault.application.dto.parse import ParsedInfo

_CANONICAL_DURARARA = "Durarara!!"

# ``N화`` 뒤에 ``(TBS …)``·해상도 등이 오는 경우가 많아 끝 앵커($)는 쓰지 않는다.
_EPISODE_HWA = re.compile(r"(\d+)\s*화")
# ``듀라라라 (릴즈…)`` 꼬리 — 화차 제거 후 남는 괄호만 정리(본편 제목은 ``듀라라라``로 통일).
_DR_KR_PAREN_TAIL = re.compile(r"\s*\([^)]*\)\s*$")
# Bleach 14th TV 2010 DVDRip-Hi …
_ORDINAL_TV_YEAR_TAIL = re.compile(
    r"\s+\d+(?:st|nd|rd|th)\s+TV\s+\d{4}.*$",
    re.I,
)
_ORDINAL_TAIL = re.compile(r"\s+(\d+)(?:st|nd|rd|th)\s*$", re.I)
_ORDINAL_TIGHT = re.compile(r"(\d+)(?:st|nd|rd|th)\s*$", re.I)
_MULTI_SPACE = re.compile(r"\s+")
_LEADING_THEATER_BRACKET = re.compile(r"^\s*\[(?:극장판|劇場版|Gekijouban)\]\s*", re.I)
_THEATER_TOKEN = re.compile(r"(?:^|\s)(?:극장판|劇場版|Gekijouban)(?:\s|$)", re.I)


def _strip_first_korean_hwa_from_title(title: str) -> tuple[str, str | None]:
    """제목에서 첫 ``N화`` 구간을 제거하고 회차 숫자를 반환한다.

    Args:
        title: 표시용 제목.

    Returns:
        (``N화``를 뺀 제목, 회차 문자열 또는 매칭 없음이면 ``None``).
    """
    m = _EPISODE_HWA.search(title)
    if not m:
        return title, None
    ep = m.group(1)
    rest = (title[: m.start()] + title[m.end() :]).strip()
    rest = _MULTI_SPACE.sub(" ", rest)
    return rest, ep


def _strip_dr_korean_paren_release_tail(title: str) -> str:
    """``듀라라라 (TBS …)`` 형 끝 괄호 릴즈 꼬리를 반복 제거한다."""
    t = title.strip()
    if not re.match(r"^듀라라라\b", t):
        return t
    while True:
        n = _DR_KR_PAREN_TAIL.sub("", t).strip()
        if n == t:
            return t
        t = n


def _strip_ordinal_tv_year_release(title: str) -> str:
    """``… 14th TV 2010 DVDRip-Hi`` 형 DVD 시즌 팩 꼬리를 뗀다.

    Args:
        title: 원본 제목.

    Returns:
        꼬리를 제거한 문자열.
    """
    return _ORDINAL_TV_YEAR_TAIL.sub("", title).strip()


def _canonicalize_durarara_family(title: str) -> str:
    """본편·x2 쿠르만 ``Durarara!!``로 통일한다. 그 외(외전 등)는 그대로 둔다.

    Args:
        title: 정리 중인 제목.

    Returns:
        통일이 필요하면 ``_CANONICAL_DURARARA``, 아니면 원본 ``title``.
    """
    raw = title.strip()
    if not raw:
        return raw
    if not re.match(r"(?i)^durarara", raw):
        return raw
    # 스핀오프·타 작품: durarara 뒤에 x2/본편이 아닌 단어
    spaced = _MULTI_SPACE.sub(" ", re.sub(r"!+", " ", raw)).strip()
    lo = spaced.lower()
    if lo == "durarara":
        return _CANONICAL_DURARARA
    m = re.match(r"^durarara x2 (ten|ketsu|shou)$", lo)
    if m:
        return _CANONICAL_DURARARA
    return raw


def _strip_theater_title_tokens(title: str) -> str:
    """극장판 표기를 제목에서 제거한다.

    Args:
        title: 정리 중인 제목.

    Returns:
        ``[극장판]`` 같은 선행 태그와 ``극장판/劇場版/Gekijouban`` 토큰을 뺀 제목.
    """
    t = title.strip()
    while True:
        n = _LEADING_THEATER_BRACKET.sub("", t).strip()
        if n == t:
            break
        t = n
    t = _THEATER_TOKEN.sub(" ", t)
    return _MULTI_SPACE.sub(" ", t).strip()


def apply_anime_title_refine(stem: str, info: ParsedInfo) -> ParsedInfo:
    """stem·초기 파싱 결과로 표시용 제목·에피소드를 다듬는다.

    Args:
        stem: 확장자 없는 파일명.
        info: FilenameParser가 만든 ``ParsedInfo``.

    Returns:
        제목·parse_group·episode가 정리된 ``ParsedInfo``.
    """
    title = (info.title or "").strip()
    episode = (info.episode or "").strip()
    season = (info.season or "").strip()
    resolution = info.resolution
    year = info.year

    m_title = _EPISODE_HWA.search(title)
    m_stem = _EPISODE_HWA.search(stem) if not m_title else None
    if m_title:
        title, ep_from_hwa = _strip_first_korean_hwa_from_title(title)
        episode = ep_from_hwa or episode
    elif m_stem:
        episode = m_stem.group(1)

    title = _strip_dr_korean_paren_release_tail(title)

    title = _strip_ordinal_tv_year_release(title)
    title = _ORDINAL_TAIL.sub("", title).strip()
    title = _ORDINAL_TIGHT.sub("", title).strip()
    title = _strip_theater_title_tokens(title)

    if not title:
        title = (info.title or "").strip()

    # 예전에 N화를 시즌으로 잡은 경우(숫자 동일) 시즌을 비운다.
    if episode and season == episode:
        season = ""

    title = _canonicalize_durarara_family(title)

    return ParsedInfo(
        title=title,
        parse_group=title,
        year=year,
        season=season,
        resolution=resolution,
        episode=episode,
    )
