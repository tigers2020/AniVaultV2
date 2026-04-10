"""Port for poster asset synchronization."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from anivault.contracts.pipeline import MatchResult, PipelineRow


@runtime_checkable
class PosterAssetSyncPort(Protocol):
    def sync_from_match_result(self, result: MatchResult) -> None: ...

    def sync_from_files(self, files: Sequence[PipelineRow]) -> None: ...
