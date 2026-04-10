"""Shared types for TMDB matching helper modules."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from anivault.contracts.progress import ProgressEvent

MatchProgressCallback = Callable[[ProgressEvent], None]
TmdbCandidateProvenance = Literal["group_db", "provider"]
