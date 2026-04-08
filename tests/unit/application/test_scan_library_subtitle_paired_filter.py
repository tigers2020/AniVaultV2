"""scan_library with exclude_subtitles_with_paired_video."""

from __future__ import annotations

from pathlib import Path
from threading import Event
from typing import Any

from anivault.application.dto.scan import ScanInput
from anivault.application.use_cases.scan_library import make_execute


class _FileRepo:
    def __init__(self, paths: list[Path]) -> None:
        self.paths = paths

    def list_files(self, *args: Any, **kwargs: Any) -> list[Path]:
        del args, kwargs
        return self.paths


def test_scan_excludes_paired_subtitles_when_flag_true(tmp_path: Path) -> None:
    (tmp_path / "show.mkv").write_bytes(b"v")
    (tmp_path / "show.srt").write_bytes(b"s")
    (tmp_path / "orphan.srt").write_bytes(b"o")

    paths = [tmp_path / "show.srt", tmp_path / "orphan.srt"]
    execute = make_execute(_FileRepo(paths), library_index=None)

    result = execute(
        ScanInput(path=str(tmp_path), exclude_subtitles_with_paired_video=True),
        None,
        Event(),
    )

    assert result.paths == [str(tmp_path / "orphan.srt")]


def test_scan_keeps_subtitles_when_flag_false(tmp_path: Path) -> None:
    (tmp_path / "show.mkv").write_bytes(b"v")
    (tmp_path / "show.srt").write_bytes(b"s")

    paths = [tmp_path / "show.srt"]
    execute = make_execute(_FileRepo(paths), library_index=None)

    result = execute(ScanInput(path=str(tmp_path)), None, Event())

    assert result.paths == [str(tmp_path / "show.srt")]
