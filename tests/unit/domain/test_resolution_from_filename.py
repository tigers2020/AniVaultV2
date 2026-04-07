"""Tests for standard resolution tier normalization."""

import pytest

from anivault.domain.rules.resolution_from_filename import (
    normalize_resolution_from_raw,
    resolution_from_filename,
)


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("[SubsPlease] Frieren - 01 (1080p).mkv", "FHD"),
        ("Movie 4K WEBRip.mkv", "UHD"),
        ("Show 8k.mkv", "8K UHD"),
        ("Show 4320p.mkv", "8K UHD"),
        ("Show 1280x720.mkv", "HD"),
        ("Show 1920x1080.mkv", "FHD"),
        ("Show 2560x1440.mkv", "QHD"),
        ("Show 3840x2160.mkv", "UHD"),
        ("Show 640x360.mkv", "SD"),
        ("Show.AC3.1280.ReRip.mkv", "HD"),
        (
            r"F:\kiwi\애니\720p\2004\블리치\Season01"
            r"\Bleach.1st.TV.2004.DVDRip-Hi.x264.AC3.1280.ReRip.EP004-nezumi.mkv",
            "HD",
        ),
    ],
)
def test_resolution_from_filename_returns_standard_tier_labels(
    filename: str, expected: str
) -> None:
    assert resolution_from_filename(filename) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("Show 960x540.mkv", "HD"),
        ("Show 1600x900.mkv", "FHD"),
        ("Show 1920x1200.mkv", "QHD"),
    ],
)
def test_resolution_from_filename_rounds_dimensions_up_to_nearest_tier(
    filename: str, expected: str
) -> None:
    assert resolution_from_filename(filename) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("360p", "SD"),
        ("480p", "SD"),
        ("576p", "SD"),
        ("720p", "HD"),
        ("1080p", "FHD"),
        ("1440p", "QHD"),
        ("2160p", "UHD"),
        ("4320p", "8K UHD"),
        ("2K", "QHD"),
        ("4K", "UHD"),
        ("8K", "8K UHD"),
        ("x720", "HD"),
        ("1280", "HD"),
        ("1920x1200", "QHD"),
    ],
)
def test_normalize_resolution_from_raw_returns_standard_tier_labels(
    raw: str, expected: str
) -> None:
    assert normalize_resolution_from_raw(raw) == expected
