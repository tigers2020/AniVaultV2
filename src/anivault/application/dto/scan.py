"""DTOs for scan use case."""

from dataclasses import dataclass, field


@dataclass
class ScanInput:
    """Input for scan_library use case."""

    path: str
    recursive: bool = True


@dataclass
class ScanResult:
    """Result from scan_library. paths and resolutions share the same order and length."""

    paths: list[str] = field(default_factory=list)
    resolutions: list[str] = field(default_factory=list)
