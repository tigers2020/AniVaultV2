"""Tests for `.env` path and TMDB API key helpers."""

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from anivault.application.dto.parse import ParsedInfo as ApplicationParsedInfo
from anivault.bootstrap import container
from anivault.bootstrap import env_file
from anivault.domain.models.parsed_info import ParsedInfo as DomainParsedInfo


class _FakePage:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class _FakePresenter:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs


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


def test_application_parse_dto_reexports_domain_parsed_info() -> None:
    """Application DTO imports should keep working after moving ParsedInfo to domain."""
    assert ApplicationParsedInfo is DomainParsedInfo


def test_domain_parsed_info_defaults_match_previous_dto_shape() -> None:
    parsed = DomainParsedInfo()

    assert parsed.title == ""
    assert parsed.parse_group == ""
    assert parsed.year == ""
    assert parsed.season == ""
    assert parsed.episode == ""
    assert parsed.resolution == ""


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
    )
