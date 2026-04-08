"""tmdb_search_query.py

TMDB TV 검색용 문자열 정규화와 대체 검색어(변형) 목록.

파일명 파서가 남긴 느낌표·릴 태그·쿠르(x2) 표기 때문에 검색이 빗나가는 경우를 줄인다.

Author: Pom Kim
"""

from __future__ import annotations

import re

_LEADING_BRACKET = re.compile(r"^\s*\[[^\]]+\]\s*")
_TRAIL_PAREN = re.compile(r"\s*\(([^)]*)\)\s*$")
_TRAIL_BRACKET = re.compile(r"\s*\[[^\]]+\]\s*$")
_MULTI_SPACE = re.compile(r"\s+")
_TECH_TOKEN = re.compile(r"[a-z0-9]+", re.I)
_RESOLUTION_TOKEN = re.compile(r"^(?:\d{3,4}p?|[248]k)$", re.I)
_TECH_HINTS = {
    "sd",
    "hd",
    "fhd",
    "qhd",
    "uhd",
    "x264",
    "x265",
    "hevc",
    "aac",
    "ac3",
    "dvd",
    "bd",
    "bluray",
}


def compact_compare_key(s: str) -> str:
    """TMDB 제목·검색어 비교용 키(공백 제거 후 소문자만 유지).

    Args:
        s: 원본 문자열.

    Returns:
        정규화된 키.
    """
    return "".join(c.lower() for c in s if not c.isspace())


def normalize_tmdb_search_query(raw: str) -> str:
    """릴·해상도 꼬리와 느낌표를 정리해 TMDB 검색어 한 줄을 만든다.

    Args:
        raw: 그룹 키(파싱된 제목 등).

    Returns:
        정리된 검색어. 빈 입력이면 빈 문자열.
    """
    s = (raw or "").strip()
    if not s:
        return ""
    for _ in range(24):
        t = _LEADING_BRACKET.sub("", s)
        if t == s:
            break
        s = t
    for _ in range(12):
        u = _strip_trailing_tech_paren(s)
        u = _TRAIL_BRACKET.sub("", u)
        if u == s:
            break
        s = u.strip()
    # TMDB 쪽 제목은 느낌표 없이 잡히는 경우가 많음 → 공백으로 나눔
    s = re.sub(r"!+", " ", s)
    s = _MULTI_SPACE.sub(" ", s).strip()
    return s


def _strip_trailing_tech_paren(text: str) -> str:
    """문자열 끝의 기술 꼬리 괄호를 감지하면 제거한다."""
    m = _TRAIL_PAREN.search(text)
    if not m:
        return text
    inner = m.group(1)
    tokens = [tok.lower() for tok in _TECH_TOKEN.findall(inner)]
    if not tokens:
        return text
    if any(t in _TECH_HINTS for t in tokens):
        return text[: m.start()].rstrip()
    if any(_RESOLUTION_TOKEN.match(t) for t in tokens):
        return text[: m.start()].rstrip()
    return text


def iter_strip_last_word_chain(query: str) -> list[str]:
    """공백으로 나뉜 토큰에서 마지막 단어를 하나씩 제거한 검색어 목록을 만든다.

    TMDB가 전체 제목으로는 0건일 때 짧은 뿌리 제목으로 재시도할 때 쓴다.
    중복(대소문자 무시)은 제거한다.

    Args:
        query: 정규화된 검색어 한 줄.

    Returns:
        긴 순·짧은 순 문자열 목록(최소 0개). 빈 입력이면 빈 목록.
    """
    s = (query or "").strip()
    if not s:
        return []
    parts = s.split()
    seen: set[str] = set()
    out: list[str] = []
    while len(parts) >= 1:
        candidate = " ".join(parts)
        key = candidate.lower()
        if key not in seen:
            seen.add(key)
            out.append(candidate)
        if len(parts) == 1:
            break
        parts = parts[:-1]
    return out


def iter_tmdb_search_queries(raw: str) -> list[str]:
    """정규화본과 짧은 뿌리(쿠르 분리 등)를 순서대로 반환한다.

    중복(대소문자 무시)은 제거한다.

    Args:
        raw: 원본 그룹 키.

    Returns:
        시도할 검색어 문자열 목록(최소 0개).
    """
    base = normalize_tmdb_search_query(raw)
    if not base:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for v in _variants(base):
        vx = v.strip()
        if not vx:
            continue
        k = vx.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(vx)
    return out


def _variants(base: str) -> list[str]:
    """정규화된 검색어에서 파생 변형을 만든다.

    Args:
        base: ``normalize_tmdb_search_query`` 결과.

    Returns:
        우선순위 순 문자열(중복 포함 가능, 호출측에서 제거).
    """
    vs: list[str] = [base]
    # Durarara x2 Ten / … x2 쿠르 → 루트만으로 재검색
    m = re.match(r"^(.+?)\s+x2\s+", base, re.I)
    if m:
        root = m.group(1).strip()
        if root:
            vs.append(root)
    return vs
