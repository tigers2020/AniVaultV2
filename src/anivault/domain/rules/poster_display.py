"""poster_display.py

파이프라인·UI용 최종 포스터 이미지 소스 문자열(로컬 우선 → CDN).

우선순위(고정):
1. 로컬 절대 경로가 주어지고 파일이 존재하면 그 경로 문자열(로더가 절대 경로 지원).
2. CDN `http(s)` URL이 비어 있지 않으면 그대로.
3. 빈 문자열.

`PipelineRow.poster_url`은 CDN만이 아니라 위 규칙으로 정해진 **최종 표시 소스**다.

Author: Pom Kim
"""

from __future__ import annotations

from pathlib import Path


def resolve_final_poster_display_source(
    local_absolute_path: str | None,
    cdn_url: str,
) -> str:
    """로컬 파일이 있으면 절대 경로, 없으면 CDN URL을 반환한다.

    Args:
        local_absolute_path: 로컬 파일 절대 경로. None·빈 문자열은 무시.
        cdn_url: TMDB 이미지 CDN 전체 URL.

    Returns:
        표시용 문자열(절대 경로 또는 http(s) 또는 "").
    """
    lp = (local_absolute_path or "").strip()
    if lp:
        try:
            if Path(lp).is_file():
                return lp
        except OSError:
            pass
    cu = (cdn_url or "").strip()
    return cu
