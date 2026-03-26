"""poster_asset_sync.py

TMDB 포스터 로컬 캐시 동기화(매칭 직후 1회). atomic 파일 쓰기 후 DB ready.

Author: Pom Kim
"""

from __future__ import annotations

import contextlib
import logging
import os
import tempfile
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

from anivault.adapters.persistence.sqlite.db_path import ensure_poster_cache_dir
from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.dto.match_result import MatchFileRow, MatchResult
from anivault.application.ports.title_match_port import TitleMatchRepository
from anivault.domain.rules.poster_cache_filename import poster_cache_file_path
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.domain.rules.tmdb_image_url import tmdb_poster_cdn_url

logger = logging.getLogger(__name__)

_USER_AGENT = "AniVault/2 (poster cache)"


def iter_unique_poster_jobs(
    files: Sequence[MatchFileRow],
) -> list[tuple[int, str]]:
    """파일 행에서 (tmdb_id, 정규화 remote_path) 유일 목록을 만든다.

    Args:
        files: 매칭 파일 행 시퀀스.

    Returns:
        중복 제거된 (tmdb_id, remote_path) 리스트.
    """
    seen: set[tuple[int, str]] = set()
    out: list[tuple[int, str]] = []
    for f in files:
        tid_s = (f.tmdb_series_id or "").strip()
        rp = normalize_tmdb_remote_image_path(f.tmdb_poster_path)
        if not tid_s or not rp:
            continue
        try:
            tid = int(tid_s)
        except ValueError:
            continue
        key = (tid, rp)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def download_image_atomic(url: str, dest: Path) -> bool:
    """URL 바이너리를 임시 파일에 쓴 뒤 rename으로 원자적으로 반영한다.

    Args:
        url: http(s) 이미지 URL.
        dest: 최종 경로.

    Returns:
        성공 여부.
    """
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        fd, tmp_name = tempfile.mkstemp(suffix=".part", dir=str(dest.parent))
        try:
            with os.fdopen(fd, "wb") as tmp_f:
                tmp_f.write(data)
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
            os.replace(tmp_name, dest)
            return True
        finally:
            if os.path.isfile(tmp_name):
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
    except (OSError, urllib.error.URLError, ValueError) as e:
        logger.warning("포스터 다운로드 실패 %s: %s", url, e)
        return False


class TmdbPosterAssetSync:
    """매칭 결과 기준 포스터 1회 다운로드·poster_assets 갱신."""

    def __init__(
        self,
        title_match: TitleMatchRepository,
        cache_dir: Path | None = None,
    ) -> None:
        """저장소와 선택적 캐시 루트를 받는다.

        Args:
            self: 이 동기화기.
            title_match: TitleMatchRepository.
            cache_dir: None이면 `ensure_poster_cache_dir()`.

        Returns:
            None.
        """
        self._title_match = title_match
        self._cache_dir = cache_dir

    def _dir(self) -> Path:
        """캐시 디렉터리 Path를 반환한다.

        Args:
            self: 이 동기화기.

        Returns:
            존재 보장된 디렉터리.
        """
        if self._cache_dir is not None:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            return self._cache_dir
        return ensure_poster_cache_dir()

    def sync_from_match_result(self, result: MatchResult) -> None:
        """MatchResult.files 기준 포스터를 채운다.

        Args:
            self: 이 동기화기.
            result: 매칭 유스케이스 결과.

        Returns:
            None.
        """
        self.sync_from_files(result.files)

    def sync_from_files(self, files: Sequence[MatchFileRow]) -> None:
        """파일 행 목록에서 유일 포스터 작업만 수행한다.

        Args:
            self: 이 동기화기.
            files: MatchFileRow 시퀀스.

        Returns:
            None.
        """
        for tmdb_id, remote in iter_unique_poster_jobs(files):
            self.ensure_poster_cached(tmdb_id, remote)

    def ensure_poster_cached(self, tmdb_id: int, remote_path: str) -> None:
        """단일 포스터가 로컬 ready이면 생략하고, 아니면 다운로드한다.

        Args:
            self: 이 동기화기.
            tmdb_id: TMDB TV id.
            remote_path: TMDB poster 상대 경로.

        Returns:
            None.
        """
        norm = normalize_tmdb_remote_image_path(remote_path)
        if not norm:
            return
        if self._title_match.get_series_candidate(tmdb_id) is None:
            logger.debug("tmdb_series 없음 poster 생략 tmdb_id=%s", tmdb_id)
            return
        lp = self._title_match.get_poster_local_path(tmdb_id, "poster", norm)
        if lp:
            return
        url = tmdb_poster_cdn_url(norm)
        if not url:
            return
        dest = poster_cache_file_path(self._dir(), tmdb_id, "poster", norm)
        ok = download_image_atomic(url, dest)
        now = utc_now_sqlite_text()
        if ok:
            self._title_match.save_poster_asset(
                tmdb_id,
                "poster",
                norm,
                local_path=str(dest.resolve()),
                status="ready",
                verified_at=now,
            )
        else:
            self._title_match.save_poster_asset(
                tmdb_id,
                "poster",
                norm,
                local_path="",
                status="failed",
                verified_at=None,
            )
