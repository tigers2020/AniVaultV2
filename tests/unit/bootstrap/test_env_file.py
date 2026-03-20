"""Tests for `.env` path and TMDB API key helpers."""

import os
from pathlib import Path

import pytest

from anivault.bootstrap import env_file


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
