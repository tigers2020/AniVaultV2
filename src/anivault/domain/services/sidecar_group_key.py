"""sidecar_group_key.py

스캔 인덱스용 사이드카 그룹 키: 동일 디렉터리·동일 stem 영상/자막을 한 키로 묶는다.

Author: Pom Kim
"""

from __future__ import annotations


def compute_sidecar_group_key(
    *,
    media_kind: str,
    dir_norm: str,
    file_stem: str,
) -> str | None:
    """dir_norm 과 file_stem 으로 안정적인 sidecar_group_key 문자열을 만들거나 None 을 반환한다.

    video·subtitle 만 키를 받으며, 그 외 media_kind 는 None 이다.

    Args:
        media_kind: `video`, `subtitle`, `other` 등.
        dir_norm: 루트 대비 디렉터리 정규화 키(`media_files.dir_norm`).
        file_stem: 확장자 제외 파일명.

    Returns:
        `\x1e` 로 dir 과 stem 을 잇은 문자열. 비디오/자막이 아니면 None.
    """
    mk = (media_kind or "").strip()
    if mk not in ("video", "subtitle"):
        return None
    d = dir_norm or ""
    s = file_stem or ""
    if not d and not s:
        return None
    return f"{d}\x1e{s}"
