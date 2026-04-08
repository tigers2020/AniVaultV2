from __future__ import annotations

from pathlib import Path

from anivault.adapters.fs.file_system_adapter import FsFileRepository


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_list_files_filters_extensions_case_insensitively(tmp_path: Path) -> None:
    _touch(tmp_path / "show.MKV")
    _touch(tmp_path / "subtitle.srt")
    _touch(tmp_path / "notes.txt")
    repo = FsFileRepository()

    result = repo.list_files(tmp_path, extensions=(".mkv", "SRT"))

    assert [path.name for path in result] == ["show.MKV", "subtitle.srt"]


def test_list_files_respects_recursive_flag(tmp_path: Path) -> None:
    _touch(tmp_path / "root.mkv")
    _touch(tmp_path / "nested" / "child.mkv")
    repo = FsFileRepository()

    recursive = repo.list_files(tmp_path, extensions=(".mkv",), recursive=True)
    shallow = repo.list_files(tmp_path, extensions=(".mkv",), recursive=False)

    assert [path.name for path in recursive] == ["child.mkv", "root.mkv"]
    assert [path.name for path in shallow] == ["root.mkv"]


def test_list_files_can_preserve_scandir_order_when_unsorted(tmp_path: Path) -> None:
    _touch(tmp_path / "b.mkv")
    _touch(tmp_path / "a.mkv")
    repo = FsFileRepository()

    result = repo.list_files(tmp_path, extensions=(".mkv",), recursive=False, sort=False)

    assert sorted(path.name for path in result) == ["a.mkv", "b.mkv"]


def test_list_files_returns_empty_for_missing_or_empty_directory(tmp_path: Path) -> None:
    repo = FsFileRepository()

    assert repo.list_files(tmp_path / "missing") == []
    assert repo.list_files(tmp_path) == []
