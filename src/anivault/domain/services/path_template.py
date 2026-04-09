"""path_template.py

설정의 path_template과 매칭 행으로 대상 경로 문자열을 만든다.

Author: Pom Kim
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from anivault.domain.models.path_template_input import PathTemplateInput

_INVALID_IN_SEGMENT = frozenset('<>:"/\\|?*')

_PLACEHOLDER = re.compile(r"\{([^}]+)\}")


def _absolute_lexical_path(path: Path) -> str:
    """Return an absolute path without resolving symlinks or touching the filesystem."""
    path_str = str(path)
    if path.is_absolute():
        return os.path.normpath(path_str)
    return os.path.abspath(path_str)


def sanitize_path_segment(segment: str) -> str:
    """단일 경로 조각에서 Windows 금지 문자를 치환한다.

    Args:
        segment: 폴더 또는 파일명 조각.

    Returns:
        안전한 조각. 비어 있거나 '.'만이면 '_'.
    """
    out = "".join("_" if c in _INVALID_IN_SEGMENT else c for c in segment)
    out = out.strip()
    if out in (".", "..") or not out:
        return "_"
    return out


def sanitize_basename(filename: str) -> str:
    """확장자를 유지한 채 파일명만 정규화한다.

    Args:
        filename: 파일명(경로 구분자 없음 권장).

    Returns:
        정규화된 파일명.
    """
    p = Path(filename)
    stem = sanitize_path_segment(p.stem)
    ext = p.suffix
    if ext:
        ext = "".join("_" if c in _INVALID_IN_SEGMENT else c for c in ext)
    return stem + ext


def _format_with_spec(raw: str, spec: str | None, *, numeric: bool) -> str:
    """플레이스홀더 포맷 접미사(:02 등)를 적용한다.

    Args:
        raw: 원본 값.
        spec: `key` 뒤의 `:02` 부분. None이면 세그먼트만 sanitize.
        numeric: True면 숫자만 추출해 자릿수 맞춤.

    Returns:
        치환된 문자열.
    """
    if not spec:
        return sanitize_path_segment(raw)
    if numeric and spec.isdigit():
        width = len(spec)
        digits = re.sub(r"\D", "", raw) or "0"
        try:
            n = int(digits)
        except ValueError:
            n = 0
        return str(n).zfill(width)
    return sanitize_path_segment(raw)


def effective_resolution_segment(resolution: str, unknown_resolution: str) -> str:
    """Return the effective resolution folder segment used by the template renderer."""
    return (resolution or "").strip() or unknown_resolution.strip() or "Unknown"


def _context_values(
    row: PathTemplateInput,
    *,
    target_root: str,
    unknown_resolution: str,
    unknown_group_folder: str,
) -> dict[str, str]:
    """템플릿 키별 원시 값을 채운다.

    Args:
        row: 경로 템플릿용 입력 행.
        target_root: 설정 target_root.
        unknown_resolution: 해상도 없을 때.
        unknown_group_folder: 한글 그룹 없을 때.

    Returns:
        키 → 값 (아직 sanitize 전일 수 있음).
    """
    res = effective_resolution_segment(row.resolution, unknown_resolution)
    year = (row.year or "").strip() or "Unknown"
    group = (row.korean_title_group or "").strip() or unknown_group_folder.strip() or "Unknown"
    season_raw = (row.season or "").strip() or "1"
    base = Path(row.original_file.replace("\\", "/")).name
    return {
        "target": (target_root or "").strip(),
        "resolution": res,
        "year": year,
        "korean_title_group": group,
        "season": season_raw,
        "original_file": base,
        "original_filename": base,
    }


def _substitute_placeholder(
    key_spec: str,
    ctx: dict[str, str],
) -> str:
    """단일 `{key}` 또는 `{key:fmt}` 를 값으로 바꾼다.

    Args:
        key_spec: `key` 또는 `key:02` 형태.
        ctx: _context_values 결과.

    Returns:
        치환된 한 조각. `target` 은 루트 경로이므로 sanitize 하지 않는다.
    """
    if ":" in key_spec:
        key, spec = key_spec.split(":", 1)
    else:
        key, spec = key_spec, None
    key = key.strip()
    raw = ctx.get(key, "")
    if key in {"original_file", "original_filename"}:
        return sanitize_basename(raw)
    if key == "season":
        return _format_with_spec(raw, spec, numeric=True)
    if key == "target":
        return (raw or "").strip()
    return _format_with_spec(raw, spec, numeric=False)


def render_destination_path(
    template: str,
    row: PathTemplateInput,
    *,
    target_root: str,
    unknown_resolution: str,
    unknown_group_folder: str,
) -> str:
    """path_template 문자열을 채워 정규화된 절대 경로 문자열을 반환한다.

    Args:
        template: 설정의 path_template.
        row: 경로 템플릿용 입력 행.
        target_root: path_rules.target_root.
        unknown_resolution: 미지정 해상도 폴더명.
        unknown_group_folder: 미지정 그룹 폴더명.

    Returns:
        목적지 절대 경로(문자열).
    """

    def repl(m: re.Match[str]) -> str:
        """단일 플레이스홀더를 치환한다.

        Args:
            m: 정규식 매치.

        Returns:
            치환 문자열.
        """
        return _substitute_placeholder(m.group(1).strip(), ctx)

    ctx = _context_values(
        row,
        target_root=target_root,
        unknown_resolution=unknown_resolution,
        unknown_group_folder=unknown_group_folder,
    )
    out = _PLACEHOLDER.sub(repl, template)
    p = Path(out)
    if not p.is_absolute():
        base = Path(ctx["target"])
        p = base / p
    return _absolute_lexical_path(p)
