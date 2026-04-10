"""benchmark_bottlenecks.py

플랜(병목 분석)의 측정 to-do 구현: 스캔 구간 분해, 매칭 워커·검색 캐시 비교, GUI modelReset 동기화 시간.

로컬 실행 예:
  python scripts/benchmark_bottlenecks.py scan --count 500
  python scripts/benchmark_bottlenecks.py match --groups 80 --stub-delay 0.012
  ANIVAULT_BENCHMARK_HEADLESS=1 python scripts/benchmark_bottlenecks.py gui --flat-count 2000

Author: Pom Kim
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from threading import Event

from anivault.adapters.fs.file_system_adapter import FsFileRepository
from anivault.adapters.metadata.tmdb.caching_metadata_provider import CachingMetadataProvider
from anivault.adapters.persistence.sqlite import (
    SqliteLibraryIndexRepository,
    SqliteParseCacheRepository,
    SqliteTitleMatchRepository,
    create_connection,
)
from anivault.application.ports.metadata_provider import MetadataProvider
from anivault.application.use_cases.match_series import make_execute as make_match_execute
from anivault.application.use_cases.scan_library import (
    _collect_resolutions_after_scan,
    _try_persist_library_index,
)
from anivault.contracts.pipeline import MatchInput, PipelineRow
from anivault.contracts.tmdb import TmdbSeriesCandidate
from anivault.domain.media.extensions import VIDEO_SCAN_EXTENSIONS


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
    batch.mkdir(parents=True, exist_ok=True)
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
    ) -> Sequence[TmdbSeriesCandidate]:
        """짧은 지연 뒤 빈 결과를 반환한다.

        Args:
            self: 이 스텁.
            query: 검색어(무시).
            year: 연도(무시).

        Returns:
            빈 시퀀스.
        """
        del query, year
        time.sleep(self._delay_s)
        return ()


def _run_scan_segments(count: int) -> int:
    """스캔을 list_files / 인덱스 persist / resolve 조회 / 해상도 수집으로 나누어 출력한다.

    Args:
        count: 더미 .mkv 개수.

    Returns:
        종료 코드(0).
    """
    with tempfile.TemporaryDirectory() as tmp_base:
        tmp_base_path = Path(tmp_base)
        db_path = tmp_base_path / "bench.db"
        media_root = tmp_base_path / "media"
        _write_dummy_tree(media_root, count)

        conn = create_connection(db_path)
        lock = threading.Lock()
        library_index = SqliteLibraryIndexRepository(conn, lock)
        parse_cache = SqliteParseCacheRepository(conn, lock)
        file_repo = FsFileRepository()
        cancel = Event()
        scan_root_str = str(media_root)

        t0 = time.perf_counter()
        paths = file_repo.list_files(
            media_root,
            extensions=VIDEO_SCAN_EXTENSIONS,
            recursive=True,
            progress_callback=None,
            sort=True,
        )
        t_list = time.perf_counter()
        root_id = _try_persist_library_index(
            library_index,
            scan_root_str=scan_root_str,
            paths=paths,
            cancel_token=cancel,
        )
        t_persist = time.perf_counter()
        str_paths = [str(p) for p in paths]
        if root_id is None:
            print("  error: index persist returned None")
            conn.close()
            return 1
        resolved = library_index.resolve_media_for_parse(root_id, str_paths)
        t_resolve = time.perf_counter()
        resolutions = _collect_resolutions_after_scan(
            str_paths,
            resolved,
            parse_cache,
            None,
            None,
            cancel,
        )
        t_res_loop = time.perf_counter()
        conn.close()

    print(f"scan segments (files={count}, resolution_probe=None, no ffprobe):")
    print(f"  list_files:           {t_list - t0:.4f}s")
    print(f"  index upsert session: {t_persist - t_list:.4f}s")
    print(f"  resolve_media_parse: {t_resolve - t_persist:.4f}s")
    print(f"  collect_resolutions: {t_res_loop - t_resolve:.4f}s")
    print(f"  total:               {t_res_loop - t0:.4f}s")
    if resolutions is None:
        print("  note: resolutions collection returned None (cancelled)")
    return 0


def _match_rows_stub(groups: int, files_per_group: int) -> list[PipelineRow]:
    """그룹 수에 맞춰 MatchFileRow 목록을 생성한다.

    Args:
        groups: 서로 다른 parse_group 키 개수.
        files_per_group: 그룹당 파일 수.

    Returns:
        평탄화된 파일 행 목록.
    """
    rows: list[PipelineRow] = []
    for g in range(groups):
        for j in range(files_per_group):
            rows.append(
                PipelineRow(
                    original_file=f"C:/dummy/show_{g:04d}_e{j + 1}.mkv",
                    parsed_title=f"Title{g}",
                    parse_group=f"group-{g}",
                    tmdb_korean_title_group="",
                    tmdb_series_id="",
                    tmdb_poster_path="",
                    tmdb_backdrop_path="",
                    year="",
                    season="",
                    resolution="1080p",
                    status="",
                    poster_url="",
                    backdrop_url="",
                    target_path="",
                    episode=str(j + 1),
                )
            )
    return rows


def _run_match_matrix(groups: int, stub_delay_s: float) -> int:
    """MATCH_MAX_WORKERS와 CachingMetadataProvider on/off에 따른 벽시계 시간을 표로 출력한다.

    Args:
        groups: 고유 parse_group 수(검색 호출 수에 준함).
        stub_delay_s: 스텁 search_series 지연(초).

    Returns:
        종료 코드(0).
    """
    workers_list = [1, 2, 4, 8]
    print(
        f"match matrix (groups={groups}, stub_delay={stub_delay_s}s per search, "
        "title_match present for cache+w persist)",
    )
    header = ["workers", "inner_stub_s", "caching_provider_s", "ratio_cache/inner"]
    print(" | ".join(f"{h:>22}" for h in header))
    for w in workers_list:
        os.environ["ANIVAULT_MATCH_MAX_WORKERS"] = str(w)
        times_inner: list[float] = []
        times_cache: list[float] = []
        for _rep in range(3):
            with tempfile.TemporaryDirectory() as tmp_base:
                tmp_base_path = Path(tmp_base)
                db_path = tmp_base_path / "m.db"
                conn = create_connection(db_path)
                lock = threading.Lock()
                title_match = SqliteTitleMatchRepository(conn, lock)
                rows = _match_rows_stub(groups, 1)
                cancel = Event()
                provider_inner: MetadataProvider = _SlowStubMetadataProvider(stub_delay_s)
                ex_inner = make_match_execute(
                    provider_inner,
                    title_match=title_match,
                    title_groups=None,
                    poster_sync=None,
                )
                t0 = time.perf_counter()
                ex_inner(
                    MatchInput(files=tuple(rows), index_root_id=None),
                    None,
                    cancel,
                )
                times_inner.append(time.perf_counter() - t0)
                conn.close()
            with tempfile.TemporaryDirectory() as tmp_base:
                tmp_base_path = Path(tmp_base)
                db_path = tmp_base_path / "m2.db"
                conn = create_connection(db_path)
                lock = threading.Lock()
                title_match = SqliteTitleMatchRepository(conn, lock)
                rows = _match_rows_stub(groups, 1)
                cancel = Event()
                inner = _SlowStubMetadataProvider(stub_delay_s)
                wrapped = CachingMetadataProvider(inner, title_match, language="ko-KR")
                ex_cache = make_match_execute(
                    wrapped,
                    title_match=title_match,
                    title_groups=None,
                    poster_sync=None,
                )
                t0 = time.perf_counter()
                ex_cache(
                    MatchInput(files=tuple(rows), index_root_id=None),
                    None,
                    cancel,
                )
                times_cache.append(time.perf_counter() - t0)
                conn.close()
        inner_med = sorted(times_inner)[len(times_inner) // 2]
        cache_med = sorted(times_cache)[len(times_cache) // 2]
        ratio = cache_med / inner_med if inner_med > 0 else 0.0
        print(
            f"{w:>22} | {inner_med:>22.4f} | {cache_med:>22.4f} | {ratio:>22.3f}",
        )
    print("  (median of 3 runs per cell; fresh DB each run - search cache cold for wrapper path)")
    return 0


def _run_gui_sync(flat_count: int) -> int:
    """PipelineResultPanel에서 modelReset→_sync_views_from_model 경로 시간을 잰다.

    Args:
        flat_count: PipelineRow 개수(각기 다른 parse_group으로 그룹 행 수≈flat_count).

    Returns:
        종료 코드(0).
    """
    if os.environ.get("ANIVAULT_BENCHMARK_HEADLESS"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from anivault.interfaces.gui.models import (
        PipelineGroupRow,
        PipelineTableModel,
        group_pipeline_rows,
    )
    from anivault.interfaces.gui.templates.pipeline_result_panel import PipelineResultPanel

    _ = QApplication.instance() or QApplication(sys.argv)
    model = PipelineTableModel()
    _panel = PipelineResultPanel(model=model)

    flat: list[PipelineRow] = []
    for i in range(flat_count):
        flat.append(
            PipelineRow(
                original_file=f"/d/f_{i}.mkv",
                parsed_title=f"T{i}",
                parse_group=f"g{i}",
                tmdb_korean_title_group="한글" if i % 2 == 0 else "",
                tmdb_series_id="",
                tmdb_poster_path="",
                tmdb_backdrop_path="",
                year="",
                season="",
                resolution="1080p",
                status="s",
                poster_url="",
                backdrop_url="",
                target_path="",
                episode="1",
            )
        )
    grouped: list[PipelineGroupRow] = group_pipeline_rows(flat)
    t0 = time.perf_counter()
    model.set_rows(grouped)
    dt = time.perf_counter() - t0
    print(
        f"gui modelReset sync: flat_rows={flat_count}, group_rows={len(grouped)}, "
        f"set_rows wall={dt:.4f}s (includes handler _sync_views_from_model)",
    )
    del _panel
    return 0


def main() -> int:
    """서브커맨드 scan | match | gui 를 파싱해 벤치마크를 실행한다.

    Args:
        없음.

    Returns:
        프로세스 종료 코드.
    """
    parser = argparse.ArgumentParser(description="AniVault bottleneck measurement harness.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="Time scan sub-phases (dummy tree).")
    p_scan.add_argument("--count", type=int, default=500)

    p_match = sub.add_parser("match", help="Match workers x caching provider matrix.")
    p_match.add_argument("--groups", type=int, default=80)
    p_match.add_argument("--stub-delay", type=float, default=0.012)

    p_gui = sub.add_parser("gui", help="Time PipelineResultPanel model sync.")
    p_gui.add_argument("--flat-count", type=int, default=2000)

    args = parser.parse_args()
    if args.cmd == "scan":
        return _run_scan_segments(args.count)
    if args.cmd == "match":
        return _run_match_matrix(args.groups, args.stub_delay)
    if args.cmd == "gui":
        return _run_gui_sync(args.flat_count)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
