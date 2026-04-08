from __future__ import annotations

from pathlib import Path

import pytest

from anivault.domain.path_norm import (
    dir_norm_for_relative,
    infer_dest_library_root,
    normalize_path_key,
    relative_posix_under_root,
)


def test_normalize_path_key_trims_trailing_slash() -> None:
    normalized = normalize_path_key("folder/subfolder/")

    assert normalized.replace("\\", "/").endswith("folder/subfolder")
    assert not normalized.endswith("/")
    assert not normalized.endswith("\\")


def test_infer_dest_library_root_uses_first_divergent_directory(tmp_path: Path) -> None:
    source_root = tmp_path / "library" / "anime"
    new_file = tmp_path / "organized" / "FHD" / "Show" / "episode.mkv"
    source_root.mkdir(parents=True)
    new_file.parent.mkdir(parents=True)
    new_file.write_text("x", encoding="utf-8")

    root = infer_dest_library_root(source_root, new_file)

    assert root == tmp_path / "organized"


def test_infer_dest_library_root_returns_parent_when_new_path_shorter(tmp_path: Path) -> None:
    source_root = tmp_path / "library" / "anime"
    new_file = tmp_path / "library" / "episode.mkv"
    source_root.mkdir(parents=True)
    new_file.write_text("x", encoding="utf-8")

    assert infer_dest_library_root(source_root, new_file) == new_file


def test_relative_posix_under_root_returns_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "library"
    file_path = root / "Season 1" / "episode.mkv"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("x", encoding="utf-8")

    assert relative_posix_under_root(root, file_path) == "Season 1/episode.mkv"


def test_relative_posix_under_root_raises_for_path_outside_root(tmp_path: Path) -> None:
    root = tmp_path / "library"
    other = tmp_path / "other" / "episode.mkv"
    root.mkdir()
    other.parent.mkdir(parents=True)
    other.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="path not under root"):
        relative_posix_under_root(root, other)


def test_dir_norm_for_relative_handles_root_and_nested_path() -> None:
    assert dir_norm_for_relative("episode.mkv") == ""
    assert dir_norm_for_relative("Season 1/episode.mkv") == "Season 1"
