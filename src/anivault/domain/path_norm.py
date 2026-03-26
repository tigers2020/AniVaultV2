"""path_norm.py

라이브러리 인덱스용 경로 정규화(`path_norm`, `dir_norm`). implementation_policy §2.

Author: Pom Kim
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def normalize_path_key(path: str | Path) -> str:
    """비교·UNIQUE용 절대 경로 키를 만든다.

    `resolve()` 후 POSIX 슬래시, 끝 `/` 제거(드라이브 루트 `C:/`는 유지). Windows에서는 `os.path.normcase`로 대소문자 통일.

    Args:
        path: 절대 또는 상대 경로.

    Returns:
        정규화된 키 문자열.

    Raises:
        OSError: `resolve()` 실패 시 전파될 수 있음.
    """
    p = Path(path).expanduser()
    try:
        resolved = p.resolve()
    except OSError:
        resolved = p
    s = resolved.as_posix()
    if len(s) > 1 and s.endswith("/"):
        s = s.rstrip("/")
        if s.endswith(":"):  # Windows 드라이브만 남은 비정상 케이스 방지
            s = s + "/"
    if os.name == "nt" or sys.platform.startswith("win"):
        return os.path.normcase(s)
    return s


def relative_posix_under_root(root: str | Path, absolute: str | Path) -> str:
    """루트 대비 상대 경로(POSIX, `.`/`..` 없이).

    Args:
        root: 라이브러리 루트.
        absolute: 파일 절대 경로.

    Returns:
        POSIX 상대 경로 문자열.

    Raises:
        ValueError: `absolute`가 `root` 밖이면.
    """
    r = Path(root).expanduser().resolve()
    a = Path(absolute).expanduser().resolve()
    try:
        rel = a.relative_to(r)
    except ValueError as e:
        raise ValueError(f"path not under root: {a} vs {r}") from e
    return rel.as_posix()


def dir_norm_for_relative(relative_posix: str) -> str:
    """`relative_path`의 부모 디렉터리 정규화 키(POSIX).

    Args:
        relative_posix: 루트 기준 상대 경로.

    Returns:
        부모 경로. 파일이 루트에 있으면 빈 문자열.
    """
    p = Path(relative_posix)
    parent = p.parent
    if parent == Path("."):
        return ""
    return parent.as_posix()
