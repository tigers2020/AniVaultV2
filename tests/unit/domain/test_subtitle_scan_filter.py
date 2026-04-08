"""Tests for filter_subtitle_paths_without_paired_video."""

from __future__ import annotations

from pathlib import Path

from anivault.domain.services.subtitle_scan_filter import filter_subtitle_paths_without_paired_video


def test_drops_subtitle_when_same_stem_video_in_folder(tmp_path: Path) -> None:
    (tmp_path / "show.mkv").write_bytes(b"v")
    (tmp_path / "show.srt").write_bytes(b"s")
    (tmp_path / "only.srt").write_bytes(b"o")

    paths = [tmp_path / "show.srt", tmp_path / "only.srt"]
    assert filter_subtitle_paths_without_paired_video(paths) == [tmp_path / "only.srt"]


def test_preserves_order_and_unpaired(tmp_path: Path) -> None:
    (tmp_path / "x.mkv").write_bytes(b"v")
    (tmp_path / "x.srt").write_bytes(b"s")
    (tmp_path / "y.srt").write_bytes(b"o")

    paths = [tmp_path / "y.srt", tmp_path / "x.srt"]
    assert filter_subtitle_paths_without_paired_video(paths) == [tmp_path / "y.srt"]


def test_mismatched_stem_keeps_subtitle(tmp_path: Path) -> None:
    (tmp_path / "video.mkv").write_bytes(b"v")
    (tmp_path / "other.srt").write_bytes(b"s")

    paths = [tmp_path / "other.srt"]
    assert filter_subtitle_paths_without_paired_video(paths) == paths


def test_empty_input() -> None:
    assert filter_subtitle_paths_without_paired_video([]) == []
