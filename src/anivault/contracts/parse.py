"""Parse use-case contracts."""

from dataclasses import dataclass, field

from anivault.domain.models import ParsedInfo


@dataclass(slots=True)
class ParseInput:
    """Input for title parsing."""

    paths: list[str] = field(default_factory=list)
    index_root_id: int | None = None


@dataclass(slots=True)
class ParseResult:
    """Output for title parsing."""

    parsed: list[ParsedInfo] = field(default_factory=list)
    cache_hits: list[bool] = field(default_factory=list)
