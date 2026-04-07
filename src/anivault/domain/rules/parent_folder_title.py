"""parent_folder_title.py

파일명만으로는 작품명이 빈약할 때(회차·에피소드만 등) 부모 폴더명을 시리즈 힌트로 쓴다.

Author: Pom Kim
"""

from __future__ import annotations

import re
from pathlib import Path

from anivault.domain.models.parsed_info import ParsedInfo

_EP_DIGITS = re.compile(r"^\d{1,4}$")
_EP_TAG = re.compile(r"^ep\s*\d+$", re.I)
_EPISODE_WORD = re.compile(r"^episode\s*$", re.I)


def augment_parsed_info_with_parent_folder(full_path: str, info: ParsedInfo) -> ParsedInfo:
    """약한 제목이면 부모 폴더 이름을 앞에 붙이거나 대체한다.

    Args:
        full_path: 스캔된 파일의 전체 경로.
        info: 파일명만으로 얻은 파싱 결과.

    Returns:
        보강이 필요 없으면 ``info`` 그대로, 아니면 제목·그룹이 갱신된 새 ``ParsedInfo``.
    """
    path = Path(full_path)
    stem = path.stem
    parent = path.parent.name
    title = (info.title or "").strip()
    if not _is_weak_title(title, stem):
        return info
    if not _is_valid_series_folder(parent):
        return info
    merged = _merge_parent_folder(parent, title)
    if merged == title:
        return info
    return ParsedInfo(
        title=merged,
        parse_group=merged,
        year=info.year,
        season=info.season,
        episode=info.episode,
        resolution=info.resolution,
    )


def _is_weak_title(title: str, stem: str) -> bool:
    """회차·숫자만 등 검색에 부적합한 제목인지 판별한다.

    Args:
        title: 파서가 낸 제목.
        stem: 확장자 없는 파일명.

    Returns:
        약한 제목이면 True.
    """
    t = (title or "").strip()
    if not t:
        return True
    if _EP_DIGITS.match(t):
        return True
    if _EP_TAG.match(t):
        return True
    if _EPISODE_WORD.match(t):
        return True
    return bool(t.lower() == stem.lower() and _EP_DIGITS.match(stem))


def _is_valid_series_folder(name: str) -> bool:
    """시리즈 폴더로 쓸 만한 이름인지 본다.

    Args:
        name: 부모 디렉터리 베이스명.

    Returns:
        힌트로 쓰기에 적합하면 True.
    """
    n = (name or "").strip()
    if len(n) < 2:
        return False
    if n.isdigit():
        return False
    low = n.lower()
    return low not in {
        "season",
        "seasons",
        "special",
        "specials",
        "sp",
        "extra",
        "extras",
        "cd",
        "disc",
        "disk",
        "vol",
        "volume",
        "part",
        "애니",
        "anime",
        "tv",
        "ova",
        "movie",
        "movies",
    }


def _merge_parent_folder(parent: str, old_title: str) -> str:
    """부모 폴더와 기존 제목을 합친다.

    Args:
        parent: 부모 폴더명.
        old_title: 기존 파싱 제목.

    Returns:
        합친 제목 문자열.
    """
    p = parent.strip()
    t = (old_title or "").strip()
    if _EP_DIGITS.match(t) or _EP_TAG.match(t) or _EPISODE_WORD.match(t):
        return p
    if not t:
        return p
    return f"{p} {t}".strip()
