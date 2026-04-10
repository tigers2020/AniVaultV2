"""Scan use-case contracts."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ScanInput:
    """Input for library scanning."""

    path: str
    recursive: bool = True
    sort_paths: bool = True
    exclude_subtitles_with_paired_video: bool = False


@dataclass(slots=True)
class ScanResult:
    """Output for library scanning."""

    paths: list[str] = field(default_factory=list)
    resolutions: list[str] = field(default_factory=list)
    index_root_id: int | None = None
