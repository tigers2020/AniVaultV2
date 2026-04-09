from __future__ import annotations

from pathlib import Path

from anivault.domain.models import ParsedInfo
from anivault.domain.rules.anime_title_refine import apply_anime_title_refine
from anivault.domain.rules.parent_folder_title import augment_parsed_info_with_parent_folder
from anivault.domain.services.companion_subtitles import companion_subtitle_operations


def test_apply_anime_title_refine_covers_episode_ordinals_and_durarara() -> None:
    info = ParsedInfo(
        title="Bleach 14th TV 2010 DVDRip-Hi 3화",
        parse_group="",
        year="2010",
        season="3",
        episode="",
        resolution="1080p",
    )
    refined = apply_anime_title_refine("Bleach 14th TV 2010 DVDRip-Hi", info)
    assert refined.title == "Bleach"
    assert refined.episode == "3"
    assert refined.season == ""

    durarara = apply_anime_title_refine(
        "Durarara!! x2 Ten",
        ParsedInfo(
            title="Durarara!! x2 Ten", parse_group="", year="", season="", episode="", resolution=""
        ),
    )
    assert durarara.title == "Durarara!!"

    theater = apply_anime_title_refine(
        "[극장판] Gekijouban Foo",
        ParsedInfo(
            title="[극장판] Gekijouban Foo",
            parse_group="",
            year="",
            season="",
            episode="",
            resolution="",
        ),
    )
    assert theater.title == "Foo"


def test_parent_folder_title_uses_parent_only_for_weak_titles() -> None:
    info = ParsedInfo(title="01", parse_group="", year="", season="", episode="01", resolution="")
    augmented = augment_parsed_info_with_parent_folder("F:/Anime/Frieren/01.mkv", info)
    assert augmented.title == "Frieren"

    unchanged = augment_parsed_info_with_parent_folder(
        "F:/Anime/Season/01.mkv",
        ParsedInfo(
            title="Strong Title", parse_group="", year="", season="", episode="", resolution=""
        ),
    )
    assert unchanged.title == "Strong Title"

    merged = augment_parsed_info_with_parent_folder(
        "F:/Anime/Frieren/episode.mkv",
        ParsedInfo(title="Episode", parse_group="", year="", season="", episode="", resolution=""),
    )
    assert merged.title == "Frieren"


def test_companion_subtitle_operations_moves_matching_sidecars(tmp_path: Path) -> None:
    source = tmp_path / "show.mkv"
    source.write_bytes(b"video")
    same_stem = tmp_path / "show.srt"
    same_stem.write_text("sub", encoding="utf-8")
    wrong_ext = tmp_path / "show.txt"
    wrong_ext.write_text("note", encoding="utf-8")
    different = tmp_path / "other.ass"
    different.write_text("sub", encoding="utf-8")

    ops = companion_subtitle_operations(str(source), str(tmp_path / "Library" / "show.mkv"))

    assert len(ops) == 1
    assert ops[0].source_path == str(same_stem)
    assert ops[0].destination_path.endswith(str(Path("Library") / "show.srt"))
