from __future__ import annotations

from anivault.adapters.parser import title_parser
from anivault.adapters.parser.title_parser import (
    AnitopyTitleParser,
    MinimalTitleParser,
    _anitopy_field_str,
    _clean_title,
    _extract_season_episode,
    _extract_year,
)


def test_clean_title_removes_tokens_and_numeric_words() -> None:
    cleaned = _clean_title("Show.1080p.-.01", {"1080p"})

    assert cleaned == "Show"


def test_extract_season_episode_handles_joined_pattern() -> None:
    assert _extract_season_episode("Series.S02E05.1080p") == ("2", "5")


def test_extract_season_episode_handles_subsplease_s2_dash_episode_pattern() -> None:
    assert _extract_season_episode(
        "[SubsPlease] The Beginning After the End S2 - 02 (1080p) [65B6C373]"
    ) == ("2", "2")


def test_extract_year_finds_year_in_filename() -> None:
    assert _extract_year("Movie.2024.BDRip") == "2024"


def test_anitopy_field_str_flattens_nested_lists() -> None:
    assert _anitopy_field_str(["1080p", ["x265", None]]) == "1080p x265"


def test_minimal_title_parser_uses_fallback_title_and_resolution() -> None:
    parsed = MinimalTitleParser(ignore_tokens="1080p,bluray").parse("Show.S01E03.1080p.mkv")

    assert parsed.title == "Show S01E03"
    assert parsed.parse_group == "Show S01E03"
    assert parsed.season == "1"
    assert parsed.episode == "3"
    assert parsed.episode_numbers == [3]
    assert parsed.resolution == "FHD"


def test_anitopy_title_parser_uses_anitopy_fields_when_available(monkeypatch) -> None:
    monkeypatch.setattr(
        title_parser.anitopy,
        "parse",
        lambda stem: {
            "anime_title": "Frieren",
            "anime_year": "2023",
            "episode_number": "01",
            "video_resolution": ["1080p"],
        },
    )

    parsed = AnitopyTitleParser().parse("[SubsPlease] Frieren - S01E01.mkv")

    assert parsed.title == "Frieren"
    assert parsed.parse_group == "Frieren"
    assert parsed.year == "2023"
    assert parsed.season == "1"
    assert parsed.episode == "1"
    assert parsed.episode_numbers == [1]
    assert parsed.resolution == "FHD"


def test_anitopy_title_parser_falls_back_when_anitopy_raises(monkeypatch) -> None:
    monkeypatch.setattr(
        title_parser.anitopy, "parse", lambda stem: (_ for _ in ()).throw(ValueError())
    )

    parsed = AnitopyTitleParser(ignore_tokens="1080p").parse("Show.S01E02.1080p.2025.mkv")

    assert parsed.title == "Show S01E02"
    assert parsed.year == "2025"
    assert parsed.season == "1"
    assert parsed.episode == "2"


def test_anitopy_title_parser_falls_back_when_title_missing(monkeypatch) -> None:
    monkeypatch.setattr(title_parser.anitopy, "parse", lambda stem: {"anime_title": ""})

    parsed = AnitopyTitleParser().parse("Fallback.Show.S01E04.mkv")

    assert parsed.title == "Fallback Show S01E04"


def test_anitopy_title_parser_preserves_reported_season_two_filename() -> None:
    parsed = AnitopyTitleParser().parse(
        "[SubsPlease] The Beginning After the End S2 - 02 (1080p) [65B6C373].mkv"
    )

    assert parsed.title == "The Beginning After the End"
    assert parsed.season == "2"
    assert parsed.episode == "2"
    assert parsed.episode_numbers == [2]
    assert parsed.resolution == "FHD"


def test_anitopy_title_parser_treats_episode_only_release_as_no_season() -> None:
    parsed = AnitopyTitleParser().parse(
        "[SubsPlease] Re Zero kara Hajimeru Isekai Seikatsu - 67 (1080p) [5BDCA671].mkv"
    )

    assert parsed.title == "Re Zero kara Hajimeru Isekai Seikatsu"
    assert parsed.season == ""
    assert parsed.episode == "67"
    assert parsed.episode_numbers == [67]
    assert parsed.resolution == "FHD"


def test_anitopy_title_parser_expands_episode_range_without_season() -> None:
    parsed = AnitopyTitleParser().parse("[SubsPlease] Example Show - 01-03 (1080p) [ABC12345].mkv")

    assert parsed.title == "Example Show"
    assert parsed.season == ""
    assert parsed.episode == "1-3"
    assert parsed.episode_numbers == [1, 2, 3]
    assert parsed.resolution == "FHD"


def test_minimal_title_parser_expands_episode_range_without_season() -> None:
    parsed = MinimalTitleParser(ignore_tokens="1080p").parse("Example.Show.-.01-03.1080p.mkv")

    assert parsed.title == "Example Show"
    assert parsed.season == ""
    assert parsed.episode == "1-3"
    assert parsed.episode_numbers == [1, 2, 3]
