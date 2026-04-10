"""Tests for `.env` path and TMDB API key helpers."""

import os
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import Any
from unittest.mock import MagicMock

import pytest

from anivault.application.use_cases.parse_titles import make_execute as make_parse_execute
from anivault.application.use_cases.plan_moves import make_execute
from anivault.bootstrap import container, env_file
from anivault.contracts.library_index import IndexedMediaForParse
from anivault.contracts.parse import ParseInput
from anivault.contracts.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.contracts.pipeline import PipelineRow
from anivault.contracts.planning import PlanInput
from anivault.contracts.progress import ProgressEvent
from anivault.domain.models.parsed_info import ParsedInfo as DomainParsedInfo
from anivault.interfaces.gui.app import PAGE_META


class _FakePage:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _FakePresenter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


class _FailingParser:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def parse(self, filename: str) -> DomainParsedInfo:
        self.calls.append(filename)
        raise AssertionError("parser should not run on parse cache hit")


class _SuccessfulParser:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def parse(self, filename: str) -> DomainParsedInfo:
        self.calls.append(filename)
        return DomainParsedInfo(
            title=Path(filename).stem,
            parse_group=Path(filename).stem,
            year="2025",
            season="1",
            episode="01",
            episode_numbers=[1],
            resolution="1080p",
        )


class _ErrorParser:
    def parse(self, filename: str) -> DomainParsedInfo:
        raise ValueError(f"bad filename: {filename}")


class _ParseLibraryIndex:
    def __init__(self, media: list[IndexedMediaForParse | None]) -> None:
        self.media = media

    def resolve_media_for_parse(
        self,
        root_id: int,
        absolute_paths: list[str],
    ) -> list[IndexedMediaForParse | None]:
        del root_id, absolute_paths
        return self.media


class _ParseCache:
    def __init__(self, cached: dict[int, DomainParsedInfo]) -> None:
        self.cached = cached
        self.lookups: list[ParseCacheLookup] = []
        self.upserted_ok: list[int] = []
        self.upserted_errors: list[int] = []
        self.upserted_ok_many: list[ParseCacheOkWrite] = []
        self.upserted_error_many: list[ParseCacheErrorWrite] = []

    def get_valid_parse(self, media_file_id: int, signature: str) -> DomainParsedInfo | None:
        del signature
        return self.cached.get(media_file_id)

    def get_valid_parses(self, lookups: list[ParseCacheLookup]) -> dict[int, DomainParsedInfo]:
        self.lookups.extend(lookups)
        return {
            lookup.media_file_id: self.cached[lookup.media_file_id]
            for lookup in lookups
            if lookup.media_file_id in self.cached
        }

    def upsert_parse_ok(self, **kwargs: Any) -> None:
        self.upserted_ok.append(int(kwargs["media_file_id"]))

    def upsert_parse_ok_many(self, items: list[ParseCacheOkWrite]) -> None:
        self.upserted_ok_many.extend(items)
        self.upserted_ok.extend(item.media_file_id for item in items)

    def upsert_parse_error(self, **kwargs: Any) -> None:
        self.upserted_errors.append(int(kwargs["media_file_id"]))

    def upsert_parse_error_many(self, items: list[ParseCacheErrorWrite]) -> None:
        self.upserted_error_many.extend(items)
        self.upserted_errors.extend(item.media_file_id for item in items)


def _matched_row(path: Path) -> PipelineRow:
    return PipelineRow(
        original_file=str(path),
        parsed_title="Parsed",
        parse_group="Parsed",
        tmdb_korean_title_group="Korean Title",
        tmdb_series_id="123",
        tmdb_poster_path="",
        tmdb_backdrop_path="",
        year="2025",
        season="1",
        resolution="1080p",
        status="TMDB matched",
        poster_url="",
        backdrop_url="",
        target_path="",
        episode="01",
    )


def _plan_input(
    row: PipelineRow,
    target_root: Path,
    *,
    include_companion_subtitles: bool,
) -> PlanInput:
    return PlanInput(
        files=(row,),
        path_template="{korean_title_group}/Season {season:02}/{original_filename}",
        target_root=str(target_root),
        unknown_resolution="Unknown",
        unknown_group_folder="Needs_Review",
        include_companion_subtitles=include_companion_subtitles,
    )


def test_read_tmdb_api_key_empty_when_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    assert env_file.read_tmdb_api_key() == ""


def test_write_and_read_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    env_file.write_tmdb_api_key("secret123")
    assert env_file.read_tmdb_api_key() == "secret123"
    assert os.environ.get(env_file.TMDB_API_KEY) == "secret123"


def test_write_strips_whitespace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    env_file.write_tmdb_api_key("  abc  ")
    assert env_file.read_tmdb_api_key() == "abc"


def test_write_empty_removes_key_and_unsets_environ(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    env_file.write_tmdb_api_key("x")
    env_file.write_tmdb_api_key("")
    assert env_file.read_tmdb_api_key() == ""
    assert env_file.TMDB_API_KEY not in os.environ


def test_resolve_dotenv_path_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom = tmp_path / "custom.env"
    custom.write_text(f"{env_file.TMDB_API_KEY}=k\n", encoding="utf-8")
    monkeypatch.setenv("ANIVAULT_DOTENV_PATH", str(custom))
    assert env_file.resolve_dotenv_path() == custom.resolve()


def test_load_into_os_environ_does_not_override_existing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    (tmp_path / ".env").write_text(f"{env_file.TMDB_API_KEY}=fromfile\n", encoding="utf-8")
    monkeypatch.setenv(env_file.TMDB_API_KEY, "preset")
    env_file.load_into_os_environ()
    assert os.environ[env_file.TMDB_API_KEY] == "preset"


def test_load_into_os_environ_loads_file_when_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ANIVAULT_DOTENV_PATH", raising=False)
    monkeypatch.delenv(env_file.TMDB_API_KEY, raising=False)
    (tmp_path / ".env").write_text(f"{env_file.TMDB_API_KEY}=fromfile\n", encoding="utf-8")
    env_file.load_into_os_environ()
    assert os.environ.get(env_file.TMDB_API_KEY) == "fromfile"


def test_domain_parsed_info_defaults_match_previous_dto_shape() -> None:
    parsed = DomainParsedInfo()

    assert parsed.title == ""
    assert parsed.parse_group == ""
    assert parsed.year == ""
    assert parsed.season == ""
    assert parsed.episode == ""
    assert parsed.episode_numbers == []
    assert parsed.resolution == ""


def test_parse_titles_loads_valid_cache_without_running_parser() -> None:
    parser = _FailingParser()
    cached = DomainParsedInfo(
        title="Cached Title",
        parse_group="Cached Title",
        year="2025",
        season="1",
        episode="01",
        episode_numbers=[1],
        resolution="1080p",
    )
    cache = _ParseCache({7: cached})
    execute = make_parse_execute(
        parser,  # type: ignore[arg-type]
        library_index=_ParseLibraryIndex(
            [IndexedMediaForParse(id=7, path_norm="show.mkv", size_bytes=10, mtime_ns=20)]
        ),  # type: ignore[arg-type]
        parse_cache=cache,  # type: ignore[arg-type]
    )
    progress: list[ProgressEvent] = []

    result = execute(
        ParseInput(paths=["F:/media/show.mkv"], index_root_id=1),
        progress.append,
        Event(),
    )

    assert result.parsed == [cached]
    assert result.cache_hits == [True]
    assert parser.calls == []
    assert [lookup.media_file_id for lookup in cache.lookups] == [7]
    assert [event.message for event in progress] == [
        "파싱 캐시 확인 중...",
        "파싱 캐시 로딩 중 1/1",
    ]


def test_parse_titles_bulk_writes_cache_misses() -> None:
    parser = _SuccessfulParser()
    cache = _ParseCache({})
    execute = make_parse_execute(
        parser,  # type: ignore[arg-type]
        library_index=_ParseLibraryIndex(
            [IndexedMediaForParse(id=8, path_norm="show.mkv", size_bytes=10, mtime_ns=20)]
        ),  # type: ignore[arg-type]
        parse_cache=cache,  # type: ignore[arg-type]
    )

    result = execute(ParseInput(paths=["F:/media/show.mkv"], index_root_id=1), None, Event())

    assert result.cache_hits == [False]
    assert parser.calls == ["show.mkv"]
    assert [item.media_file_id for item in cache.upserted_ok_many] == [8]
    assert cache.upserted_error_many == []


def test_parse_titles_bulk_writes_parse_errors() -> None:
    cache = _ParseCache({})
    execute = make_parse_execute(
        _ErrorParser(),  # type: ignore[arg-type]
        library_index=_ParseLibraryIndex(
            [IndexedMediaForParse(id=9, path_norm="bad.mkv", size_bytes=10, mtime_ns=20)]
        ),  # type: ignore[arg-type]
        parse_cache=cache,  # type: ignore[arg-type]
    )

    result = execute(ParseInput(paths=["F:/media/bad.mkv"], index_root_id=1), None, Event())

    assert result.cache_hits == [False]
    assert [item.media_file_id for item in cache.upserted_error_many] == [9]
    assert cache.upserted_error_many[0].error_code == "ValueError"


def test_create_settings_page_wires_presenter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(container, "SettingsPage", _FakePage)
    monkeypatch.setattr(container, "SettingsPresenter", _FakePresenter)

    page = container.create_settings_page()

    assert isinstance(page, _FakePage)
    assert isinstance(page.kwargs["presenter"], _FakePresenter)


def test_create_organizer_page_delegates_to_shared_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = MagicMock(return_value="page")
    model = object()
    progress_dialog = object()
    monkeypatch.setattr(container, "_create_organizer_page", builder)

    assert container.create_organizer_page(model, progress_dialog) == "page"
    builder.assert_called_once_with(
        pipeline_model=model,
        progress_dialog=progress_dialog,
        scan_extensions=None,
        include_companion_subtitles=True,
    )


def test_create_subtitle_organizer_page_delegates_to_shared_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    builder = MagicMock(return_value="page")
    model = object()
    progress_dialog = object()
    monkeypatch.setattr(container, "_create_organizer_page", builder)

    assert container.create_subtitle_organizer_page(model, progress_dialog) == "page"
    builder.assert_called_once_with(
        pipeline_model=model,
        progress_dialog=progress_dialog,
        scan_extensions=container.SUBTITLE_SCAN_EXTENSIONS,
        include_companion_subtitles=False,
        exclude_subtitles_with_paired_video=True,
    )


def test_subtitle_page_meta_describes_orphan_subtitle_workflow() -> None:
    title, description = PAGE_META["subtitles"]

    assert title == "자막만"
    assert "비디오가 누락" in description
    assert "자막 파일만" in description


def test_plan_moves_video_with_same_stem_subtitle_as_inherited_companion(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    video = source_dir / "show.mkv"
    subtitle = source_dir / "show.srt"
    non_matching_subtitle = source_dir / "other.srt"
    video.write_bytes(b"video")
    subtitle.write_text("subtitle", encoding="utf-8")
    non_matching_subtitle.write_text("other", encoding="utf-8")
    target_root = tmp_path / "organized"
    execute = make_execute()

    result = execute(
        _plan_input(_matched_row(video), target_root, include_companion_subtitles=True),
        None,
        Event(),
    )

    assert result.error is None
    assert [(move.source_path, Path(move.destination_path).name) for move in result.moves] == [
        (str(video), "show.mkv"),
        (str(subtitle), "show.srt"),
    ]
    assert (
        Path(result.moves[1].destination_path).parent
        == Path(result.moves[0].destination_path).parent
    )


def test_plan_moves_subtitle_only_does_not_expand_companions(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    subtitle = source_dir / "orphan.srt"
    companion = source_dir / "orphan.ass"
    subtitle.write_text("subtitle", encoding="utf-8")
    companion.write_text("companion", encoding="utf-8")
    target_root = tmp_path / "organized"
    execute = make_execute()

    result = execute(
        _plan_input(_matched_row(subtitle), target_root, include_companion_subtitles=False),
        None,
        Event(),
    )

    assert result.error is None
    assert [(move.source_path, Path(move.destination_path).name) for move in result.moves] == [
        (str(subtitle), "orphan.srt"),
    ]


def test_plan_moves_subtitle_only_still_requires_match_data(tmp_path: Path) -> None:
    subtitle = tmp_path / "orphan.srt"
    subtitle.write_text("subtitle", encoding="utf-8")
    row = _matched_row(subtitle)
    row = replace(row, tmdb_korean_title_group="")
    execute = make_execute()

    result = execute(
        _plan_input(row, tmp_path / "organized", include_companion_subtitles=False),
        None,
        Event(),
    )

    assert result.error is not None


def test_plan_moves_adds_resolution_preview_meta_per_subgroup(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    first = source_dir / "show-1080p.mkv"
    second = source_dir / "show-720p.mkv"
    first.write_bytes(b"1080")
    second.write_bytes(b"720")
    first_row = _matched_row(first)
    second_row = replace(_matched_row(second), resolution="720p")
    execute = make_execute()

    result = execute(
        PlanInput(
            files=(first_row, second_row),
            path_template="{resolution}/{korean_title_group}/{original_filename}",
            target_root=str(tmp_path / "organized"),
            unknown_resolution="Unknown",
            unknown_group_folder="Needs_Review",
            include_companion_subtitles=False,
        ),
        None,
        Event(),
    )

    assert result.error is None
    assert len(result.moves) == 2
    assert len(result.move_preview) == 2
    assert {meta.group_key for meta in result.move_preview} == {"tmdb:123"}
    assert {meta.group_label for meta in result.move_preview} == {"Korean Title"}
    assert {meta.resolution_segment for meta in result.move_preview} == {"1080p", "720p"}


def test_plan_moves_preview_uses_unknown_resolution_and_reuses_video_meta_for_subtitles(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    video = source_dir / "show.mkv"
    subtitle = source_dir / "show.srt"
    video.write_bytes(b"video")
    subtitle.write_text("subtitle", encoding="utf-8")
    row = replace(_matched_row(video), resolution="")
    execute = make_execute()

    result = execute(
        _plan_input(row, tmp_path / "organized", include_companion_subtitles=True),
        None,
        Event(),
    )

    assert result.error is None
    assert len(result.moves) == 2
    assert len(result.move_preview) == 2
    assert result.move_preview[0].resolution_segment == "Unknown"
    assert result.move_preview[1] == result.move_preview[0]
