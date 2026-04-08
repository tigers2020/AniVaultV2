from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FILENAMES_TXT = PROJECT_ROOT / "docs" / "filenames.txt"
SAMPLE_SIZES = (100, 1_000, 10_000)


def load_filename_samples(size: int) -> list[str]:
    if not FILENAMES_TXT.exists():
        pytest.skip(f"benchmark sample file is missing: {FILENAMES_TXT}")

    filenames = [line.strip() for line in FILENAMES_TXT.read_text(encoding="utf-8").splitlines()]
    filenames = [line for line in filenames if line]
    if filenames and filenames[0].casefold() == "collect_filenames.py":
        filenames = filenames[1:]

    if len(filenames) < size:
        pytest.skip(f"benchmark sample needs {size} filenames, found {len(filenames)}")

    return filenames[:size]


def synthetic_media_paths(root: Path, size: int) -> list[Path]:
    return [root / f"Series {i // 12:04d}" / f"Episode {i:05d} 1080p.mkv" for i in range(size)]
