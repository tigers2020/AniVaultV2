from __future__ import annotations

import subprocess
from types import SimpleNamespace

from anivault.adapters.media.ffprobe_stream_resolution import (
    FfprobeStreamResolution,
    _resolution_from_ffprobe_json,
)


def test_resolution_from_ffprobe_json_handles_invalid_payloads() -> None:
    assert _resolution_from_ffprobe_json("not json") == ""
    assert _resolution_from_ffprobe_json('{"streams": []}') == ""
    assert _resolution_from_ffprobe_json('{"streams": [{"width": "1920", "height": 1080}]}') == ""


def test_resolution_from_ffprobe_json_extracts_video_label() -> None:
    raw = '{"streams": [{"width": 1920, "height": 1080}]}'

    assert _resolution_from_ffprobe_json(raw) == "FHD"


def test_probe_display_resolution_returns_empty_without_ffprobe(monkeypatch) -> None:
    monkeypatch.setattr("anivault.adapters.media.ffprobe_stream_resolution.shutil.which", lambda _: None)

    assert FfprobeStreamResolution().probe_display_resolution("video.mkv") == ""


def test_probe_display_resolution_handles_subprocess_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.shutil.which", lambda _: "ffprobe"
    )
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.TimeoutExpired("ffprobe", 1)),
    )

    assert FfprobeStreamResolution().probe_display_resolution("video.mkv") == ""


def test_probe_display_resolution_returns_empty_on_nonzero_exit(monkeypatch) -> None:
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.shutil.which", lambda _: "ffprobe"
    )
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="bad", stdout=""),
    )

    assert FfprobeStreamResolution().probe_display_resolution("video.mkv") == ""


def test_probe_display_resolution_returns_label_on_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.shutil.which", lambda _: "ffprobe"
    )
    monkeypatch.setattr(
        "anivault.adapters.media.ffprobe_stream_resolution.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stderr="",
            stdout='{"streams": [{"width": 3840, "height": 2160}]}',
        ),
    )

    assert FfprobeStreamResolution().probe_display_resolution("video.mkv") == "UHD"
