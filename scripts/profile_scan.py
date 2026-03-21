"""profile_scan.py

임시 트리에 더미 비디오 파일을 만들고 스캔·해상도·그룹화 경로를 cProfile로 측정한다.

로컬 실행: python scripts/profile_scan.py --count 2000 [--no-sort]

Author: Pom Kim
"""

from __future__ import annotations

import argparse
import cProfile
import pstats
import sys
import tempfile
from pathlib import Path

from anivault.adapters.fs.file_system_adapter import FsFileRepository
from anivault.domain.rules.resolution_from_filename import resolution_from_filename
from anivault.interfaces.gui.models import PipelineRow, group_pipeline_rows


def _write_dummy_tree(root: Path, count: int) -> None:
    """root 아래에 .mkv 더미 파일을 count개 만든다.

    Args:
        root: 루트 디렉터리.
        count: 생성할 파일 개수.

    Returns:
        None.
    """
    root.mkdir(parents=True, exist_ok=True)
    sub = root / "batch"
    sub.mkdir(exist_ok=True)
    for i in range(count):
        name = sub / f"[Group{i % 50}] Show Name - {i + 1:04d} (1080p).mkv"
        name.write_bytes(b"")


def _run_workload(root: Path, *, sort: bool) -> None:
    """list_files → resolution → group_pipeline_rows 한 사이클을 실행한다.

    Args:
        root: 스캔 루트.
        sort: True면 정렬된 경로(어댑터 기본과 동일).

    Returns:
        None.
    """
    repo = FsFileRepository()
    paths = repo.list_files(
        root,
        extensions=(".mkv",),
        recursive=True,
        progress_callback=None,
        sort=sort,
    )
    str_paths = [str(p) for p in paths]
    resolutions = [resolution_from_filename(p) for p in str_paths]
    rows: list[PipelineRow] = []
    for p, res in zip(str_paths, resolutions, strict=True):
        rows.append(
            PipelineRow(
                original_file=p,
                parsed_title=f"Title {hash(p) % 100}",
                parse_group=f"g{hash(p) % 30}",
                tmdb_korean_title_group="",
                tmdb_series_id="",
                tmdb_poster_path="",
                tmdb_backdrop_path="",
                year="",
                season="",
                resolution=res,
                status="",
                poster_url="",
                backdrop_url="",
                target_path="",
            )
        )
    _ = group_pipeline_rows(rows)


def main() -> int:
    """CLI 진입점: 인자 파싱 후 프로파일을 실행한다.

    Args:
        없음.

    Returns:
        종료 코드 0.
    """
    parser = argparse.ArgumentParser(description="Profile scan + resolution + group path.")
    parser.add_argument("--count", type=int, default=2000, help="Number of dummy .mkv files")
    parser.add_argument(
        "--no-sort", action="store_true", help="FsFileRepository list_files(sort=False)"
    )
    parser.add_argument("--top", type=int, default=30, help="pstats lines to print")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "lib"
        _write_dummy_tree(root, args.count)
        profiler = cProfile.Profile()
        profiler.enable()
        _run_workload(root, sort=not args.no_sort)
        profiler.disable()
        stats = pstats.Stats(profiler, stream=sys.stdout).sort_stats(pstats.SortKey.CUMULATIVE)
        stats.print_stats(args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
