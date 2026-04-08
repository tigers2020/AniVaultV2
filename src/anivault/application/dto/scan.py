"""scan.py

scan_library 유스케이스용 DTO: ScanInput, ScanResult.

Author: Pom Kim
"""

from dataclasses import dataclass, field


@dataclass
class ScanInput:
    """scan_library 입력."""

    path: str
    recursive: bool = True
    sort_paths: bool = True
    exclude_subtitles_with_paired_video: bool = False


@dataclass
class ScanResult:
    """scan_library 결과. paths와 resolutions는 동일 길이·순서."""

    paths: list[str] = field(default_factory=list)
    resolutions: list[str] = field(default_factory=list)
    index_root_id: int | None = None
