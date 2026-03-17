"""DTOs for scan use case."""

from dataclasses import dataclass, field


@dataclass
class ScanInput:
    """Input for scan_library use case."""

    path: str
    recursive: bool = True


@dataclass
class ScanResult:
    """Result from scan_library. Empty for stub; Phase 1 will add scanned files."""

    paths: list[str] = field(default_factory=list)
