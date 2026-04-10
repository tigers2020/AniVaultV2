"""poster_asset_sync.py

TMDB 포스터 로컬 캐시 동기화(매칭 직후 1회). atomic 파일 쓰기 후 DB ready.

Author: Pom Kim
"""

from __future__ import annotations

import contextlib
import logging
import os
import random
import tempfile
import time
import urllib.request
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Protocol

from anivault.adapters.persistence.sqlite.db_path import ensure_poster_cache_dir
from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.ports.title_match_port import (
    PosterAssetRepository,
    TmdbSeriesRepository,
)
from anivault.constants.adapters.tmdb import (
    TMDB_POSTER_DOWNLOAD_RETRIES_DEFAULT,
    TMDB_POSTER_DOWNLOAD_RETRIES_ENV,
    TMDB_POSTER_DOWNLOAD_RETRIES_MIN,
    TMDB_POSTER_HTTP_TIMEOUT_SECONDS,
    TMDB_POSTER_MAX_WORKERS_DEFAULT,
    TMDB_POSTER_MAX_WORKERS_ENV,
    TMDB_POSTER_MAX_WORKERS_MAX,
    TMDB_POSTER_MAX_WORKERS_MIN,
    TMDB_POSTER_RETRY_BASE_DELAY_SECONDS,
    TMDB_POSTER_RETRY_JITTER_SECONDS,
    TMDB_POSTER_USER_AGENT,
)
from anivault.constants.application.statuses import (
    POSTER_ASSET_KIND_POSTER,
    POSTER_ASSET_STATUS_FAILED,
    POSTER_ASSET_STATUS_READY,
)
from anivault.contracts.pipeline import MatchResult, PipelineRow
from anivault.domain.rules.poster_cache_filename import poster_cache_file_path
from anivault.domain.rules.poster_remote_path import normalize_tmdb_remote_image_path
from anivault.domain.rules.tmdb_image_url import tmdb_poster_cdn_url

logger = logging.getLogger(__name__)


class _PosterAssetSyncRepository(TmdbSeriesRepository, PosterAssetRepository, Protocol):
    """Combined protocol for poster download coordination."""


def _poster_max_workers() -> int:
    """포스터 다운로드 동시 실행 상한을 반환한다.

    Args:
        없음.

    Returns:
        1 이상 8 이하 정수.
    """
    try:
        w = int(os.environ.get(TMDB_POSTER_MAX_WORKERS_ENV, str(TMDB_POSTER_MAX_WORKERS_DEFAULT)))
    except ValueError:
        w = TMDB_POSTER_MAX_WORKERS_DEFAULT
    return max(TMDB_POSTER_MAX_WORKERS_MIN, min(TMDB_POSTER_MAX_WORKERS_MAX, w))


def _poster_download_retries() -> int:
    """포스터 HTTP 실패 시 재시도 횟수를 반환한다.

    Args:
        없음.

    Returns:
        1 이상 정수.
    """
    try:
        r = int(
            os.environ.get(
                TMDB_POSTER_DOWNLOAD_RETRIES_ENV,
                str(TMDB_POSTER_DOWNLOAD_RETRIES_DEFAULT),
            )
        )
    except ValueError:
        r = TMDB_POSTER_DOWNLOAD_RETRIES_DEFAULT
    return max(TMDB_POSTER_DOWNLOAD_RETRIES_MIN, r)


def iter_unique_poster_jobs(
    files: Sequence[PipelineRow],
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
        req = urllib.request.Request(url, headers={"User-Agent": TMDB_POSTER_USER_AGENT})
        with urllib.request.urlopen(req, timeout=TMDB_POSTER_HTTP_TIMEOUT_SECONDS) as resp:
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
    except (OSError, ValueError) as e:
        logger.warning("포스터 다운로드 실패 %s: %s", url, e)
        return False


def download_image_atomic_with_retry(url: str, dest: Path) -> bool:
    """지수 백오프를 두고 `download_image_atomic`을 여러 번 시도한다.

    Args:
        url: http(s) 이미지 URL.
        dest: 최종 경로.

    Returns:
        한 번이라도 성공하면 True.
    """
    retries = _poster_download_retries()
    for attempt in range(retries):
        if download_image_atomic(url, dest):
            return True
        if attempt + 1 < retries:
            delay = TMDB_POSTER_RETRY_BASE_DELAY_SECONDS * (2**attempt)
            delay += random.random() * TMDB_POSTER_RETRY_JITTER_SECONDS
            time.sleep(delay)
    return False


class TmdbPosterAssetSync:
    """매칭 결과 기준 포스터 1회 다운로드·poster_assets 갱신."""

    def __init__(
        self,
        title_match: _PosterAssetSyncRepository,
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

    def sync_from_files(self, files: Sequence[PipelineRow]) -> None:
        """파일 행 목록에서 유일 포스터 작업만 수행한다.

        Args:
            self: 이 동기화기.
            files: MatchFileRow 시퀀스.

        Returns:
            None.
        """
        jobs = iter_unique_poster_jobs(files)
        if not jobs:
            return
        workers = _poster_max_workers()
        if workers <= 1:
            for tmdb_id, remote in jobs:
                self.ensure_poster_cached(tmdb_id, remote)
            return
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(self.ensure_poster_cached, tid, rp) for tid, rp in jobs]
            for fut in futures:
                fut.result()

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
        lp = self._title_match.get_poster_local_path(tmdb_id, POSTER_ASSET_KIND_POSTER, norm)
        if lp:
            return
        url = tmdb_poster_cdn_url(norm)
        if not url:
            return
        dest = poster_cache_file_path(self._dir(), tmdb_id, POSTER_ASSET_KIND_POSTER, norm)
        ok = download_image_atomic_with_retry(url, dest)
        now = utc_now_sqlite_text()
        if ok:
            self._title_match.save_poster_asset(
                tmdb_id,
                POSTER_ASSET_KIND_POSTER,
                norm,
                local_path=str(dest.resolve()),
                status=POSTER_ASSET_STATUS_READY,
                verified_at=now,
            )
        else:
            self._title_match.save_poster_asset(
                tmdb_id,
                POSTER_ASSET_KIND_POSTER,
                norm,
                local_path="",
                status=POSTER_ASSET_STATUS_FAILED,
                verified_at=None,
            )
