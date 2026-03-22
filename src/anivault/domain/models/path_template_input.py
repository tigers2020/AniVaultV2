"""path_template_input.py

경로 템플릿 치환에 필요한 파일 메타(도메인 전용).

Author: Pom Kim
"""

from dataclasses import dataclass


@dataclass(slots=True)
class PathTemplateInput:
    """path_template 플레이스홀더에 넣을 행 단위 값."""

    original_file: str
    resolution: str
    year: str
    season: str
    korean_title_group: str
