"""poster_sync_port.py

매칭 직후 포스터 로컬 캐시 동기화 포트.

Author: Pom Kim
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from anivault.application.dto.match_result import MatchFileRow, MatchResult


@runtime_checkable
class PosterAssetSyncPort(Protocol):
    """TMDB 포스터 파일 다운로드·poster_assets 반영."""

    def sync_from_match_result(self, result: MatchResult) -> None:
        """자동 매칭 결과 전체에 대해 포스터를 동기화한다.

        Args:
            self: 동기화기.
            result: MatchResult.

        Returns:
            None.
        """
        ...

    def sync_from_files(self, files: Sequence[MatchFileRow]) -> None:
        """파일 행 목록 기준으로 포스터를 동기화한다.

        Args:
            self: 동기화기.
            files: MatchFileRow 시퀀스.

        Returns:
            None.
        """
        ...
