"""profile_hot_paths.py

스캔(인덱스·해상도 캐시)·매칭(가짜 제공자)·포스터 동기화(로컬만) 구간을
monotonic 타이머와 선택적 cProfile로 측정한다.

로컬 실행:
  python scripts/profile_hot_paths.py --count 500 [--cprofile] [--top 40]

Author: Pom Kim
"""

from __future__ import annotations

import argparse
import cProfile
import os
import pstats
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from threading import Event

from anivault.adapters.fs.file_system_adapter import FsFileRepository
from anivault.adapters.metadata.tmdb.poster_asset_sync import TmdbPosterAssetSync
from anivault.adapters.persistence.sqlite import (
    SqliteLibraryIndexRepository,
    SqliteParseCacheRepository,
    SqliteTitleMatchRepository,
    create_connection,
)
from anivault.application.dto.match_result import MatchFileRow, MatchInput, MatchResult
from anivault.application.dto.scan import ScanInput
from anivault.application.dto.tmdb import TmdbSeriesCandidateDTO
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.scan_library import make_execute as make_scan_execute


def _write_dummy_tree(root: Path, count: int) -> None:
    """root 아래에 .mkv 더미 파일을 count개 만든다.

    Args:
        root: 스캔 루트.
        count: 파일 개수.

    Returns:
        None.
    """
    root.mkdir(parents=True, exist_ok=True)
    batch = root / "batch"
    batch.mkdir(exist_ok=True)
    for i in range(count):
        fp = batch / f"[Rel{i % 40}] Sample Anime - {i + 1:04d} (1080p).mkv"
        fp.write_bytes(b"")


class _SlowStubMetadataProvider:
    """네트워크를 가정한 지연만 두는 MetadataProvider."""

    def __init__(self, delay_s: float = 0.012) -> None:
        """지연 시간을 저장한다.

        Args:
            self: 이 스텁.
            delay_s: search_series 호출당 대기(초).

        Returns:
            None.
        """
        self._delay_s = delay_s

    def search_series(
        self, query: str, *, year: int | None = None
    ) -> Sequence[TmdbSeriesCandidateDTO]:
        """짧은 지연 뒤 빈 결과를 반환한다.

        Args:
            self: 이 스텁.
            query: 검색어.
            year: 연도(무시).

        Returns:
            항상 빈 시퀀스.
        """
        del query, year
        time.sleep(self._delay_s)
        return ()


def _section(name: str, t0: float) -> float:
    """구간 경과 시간을 초 단위로 출력하고 현재 시각을 반환한다.

    Args:
        name: 구간 이름.
        t0: 구간 시작 monotonic 시각.

    Returns:
        호출 시각(monotonic).
    """
    dt = time.monotonic() - t0
    print(f"  [{name}] {dt:.3f}s")
    return time.monotonic()


def main() -> int:
    """CLI: 더미 트리에서 스캔·매칭·포스터 구간을 측정한다.

    Args:
        없음.

    Returns:
        종료 코드(0).
    """
    parser = argparse.ArgumentParser(description="Profile scan / match / poster phases.")
    parser.add_argument("--count", type=int, default=500, help="Dummy .mkv file count")
    parser.add_argument("--cprofile", action="store_true", help="Run cProfile on full workload")
    parser.add_argument("--top", type=int, default=35, help="pstats lines when --cprofile")
    parser.add_argument(
        "--match-workers",
        type=int,
        default=int(os.environ.get("ANIVAULT_MATCH_MAX_WORKERS", "1")),
        help="Match ThreadPool size (env ANIVAULT_MATCH_MAX_WORKERS)",
    )
    args = parser.parse_args()

    def _run() -> None:
        with tempfile.TemporaryDirectory() as tmp_base:
            tmp_base_path = Path(tmp_base)
            db_path = tmp_base_path / "prof.db"
            media_root = tmp_base_path / "media"
            _write_dummy_tree(media_root, args.count)

            conn = create_connection(db_path)
            lock = threading.Lock()
            library_index = SqliteLibraryIndexRepository(conn, lock)
            parse_cache = SqliteParseCacheRepository(conn, lock)
            title_match = SqliteTitleMatchRepository(conn, lock)

            file_repo = FsFileRepository()
            scan_execute = make_scan_execute(
                file_repo,
                library_index=library_index,
                parse_cache=parse_cache,
                resolution_probe=None,
            )

            t0 = time.monotonic()
            cancel = Event()
            scan_result = scan_execute(
                ScanInput(path=str(media_root), recursive=True),
                None,
                cancel,
            )
            t1 = _section("scan (index + resolution cache, no ffprobe)", t0)
            print(f"    files: {len(scan_result.paths)}, index_root_id={scan_result.index_root_id}")

            rows_for_match = [
                MatchFileRow(
                    original_file=p,
                    parsed_title=f"Title{i % 50}",
                    parse_group=f"g{i % 25}",
                    tmdb_korean_title_group="",
                    tmdb_series_id="",
                    tmdb_poster_path="",
                    tmdb_backdrop_path="",
                    year="",
                    season="",
                    resolution=r or "",
                    status="",
                    poster_url="",
                    backdrop_url="",
                    target_path="",
                    episode="",
                )
                for i, (p, r) in enumerate(
                    zip(scan_result.paths, scan_result.resolutions, strict=True),
                )
            ]

            provider: MetadataProvider = _SlowStubMetadataProvider()
            match_execute = make_match_execute(
                provider,
                title_match=title_match,
                title_groups=None,
                poster_sync=None,
            )
            match_execute(
                MatchInput(
                    files=tuple(rows_for_match),
                    index_root_id=scan_result.index_root_id,
                ),
                None,
                cancel,
            )
            t2 = _section(
                f"match (stub provider ~12ms/search, workers env={args.match_workers})",
                t1,
            )

            result = MatchResult(files=tuple(rows_for_match), groups=())
            poster_sync = TmdbPosterAssetSync(title_match, cache_dir=tmp_base_path / "posters")
            poster_sync.sync_from_match_result(result)
            _section("poster sync (no HTTP; empty unique jobs)", t2)

            conn.close()

    if args.cprofile:
        profiler = cProfile.Profile()
        profiler.enable()
        _run()
        profiler.disable()
        stats = pstats.Stats(profiler, stream=sys.stdout).sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(args.top)
    else:
        wall = time.monotonic()
        _run()
        print(f"total wall: {time.monotonic() - wall:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
