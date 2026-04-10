from __future__ import annotations

from types import SimpleNamespace

from anivault.bootstrap import container as container_module
from anivault.bootstrap.container import (
    AniVaultAppContainer,
    _create_metadata_provider,
    _create_organizer_page,
    _create_parse_execute,
    _create_sqlite_repositories,
    _make_operation_log_repository,
    create_settings_page,
    make_tmdb_search_execute,
)


def test_make_tmdb_search_execute_handles_cancel_blank_and_fallback() -> None:
    provider_calls: list[tuple[str, int | None]] = []
    provider = SimpleNamespace(
        search_series=lambda query, year=None: provider_calls.append((query, year))
        or ([] if query == "show extra" else ["hit"])
    )
    execute = make_tmdb_search_execute(provider)

    cancelled = execute(
        SimpleNamespace(query="show", year=2024), None, SimpleNamespace(is_set=lambda: True)
    )
    blank = execute(
        SimpleNamespace(query="   ", year=None), None, SimpleNamespace(is_set=lambda: False)
    )
    found = execute(
        SimpleNamespace(query="show extra", year=2024), None, SimpleNamespace(is_set=lambda: False)
    )

    assert cancelled == ()
    assert blank == ()
    assert found == ("hit",)
    assert provider_calls == [("show extra", 2024), ("show", 2024)]


def test_container_factory_helpers_wire_dependencies(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(container_module, "create_connection", lambda: object())
    monkeypatch.setattr(
        container_module, "SqliteLibraryIndexRepository", lambda conn, lock: "library-index"
    )
    monkeypatch.setattr(
        container_module, "SqliteOrganizePlanRepository", lambda conn, lock: "organize-plan"
    )
    monkeypatch.setattr(
        container_module, "SqliteParseCacheRepository", lambda conn, lock: "parse-cache"
    )
    monkeypatch.setattr(
        container_module, "SqliteTitleGroupRepository", lambda conn, lock: "title-groups"
    )
    monkeypatch.setattr(
        container_module, "SqliteTitleMatchRepository", lambda conn, lock: "title-match"
    )
    monkeypatch.setattr(
        container_module,
        "SqliteTmdbSearchTvLibraryRepository",
        lambda conn, lock: "search-tv-library",
    )
    repos = _create_sqlite_repositories()
    assert repos.library_index is not None
    assert repos.organize_plan is not None
    assert repos.parse_cache is not None
    assert repos.title_groups is not None
    assert repos.title_match is not None
    assert repos.search_tv_library is not None

    monkeypatch.setattr(
        container_module, "load_all", lambda: {"parse_tmdb": {"ignore_tokens": "x264"}}
    )
    monkeypatch.setattr(
        container_module, "AnitopyTitleParser", lambda ignore_tokens="": ("parser", ignore_tokens)
    )
    monkeypatch.setattr(
        container_module, "make_parse_execute", lambda parser, **kwargs: ("execute", parser, kwargs)
    )
    parse_execute = _create_parse_execute(
        SimpleNamespace(library_index="library", parse_cache="cache")
    )
    assert parse_execute[0] == "execute"
    assert parse_execute[1] == ("parser", "x264")

    monkeypatch.setattr(
        container_module,
        "TmdbApiClient",
        lambda api_key, language="": ("client", api_key, language),
    )
    monkeypatch.setattr(
        container_module,
        "make_persist_search_tv_library_execute",
        lambda repo: ("persist-fn", repo),
    )
    monkeypatch.setattr(
        container_module,
        "TmdbMetadataProvider",
        lambda client, **kwargs: ("provider", client, kwargs),
    )
    monkeypatch.setattr(
        container_module,
        "CachingMetadataProvider",
        lambda inner, title_match, language="": ("cached", inner, title_match, language),
    )
    metadata = _create_metadata_provider(
        "key", SimpleNamespace(title_match="tmdb", search_tv_library="lib")
    )
    assert metadata[0] == "cached"

    monkeypatch.setattr(container_module, "SettingsPresenter", lambda: "presenter")
    monkeypatch.setattr(
        container_module, "SettingsPage", lambda presenter=None: ("settings-page", presenter)
    )
    settings_page = create_settings_page()
    assert settings_page == ("settings-page", "presenter")

    op_repo = _make_operation_log_repository(tmp_path)
    assert op_repo is not None


def test_create_organizer_page_handles_api_key_and_scan_extensions(monkeypatch) -> None:
    monkeypatch.setattr(container_module, "PipelineTableModel", lambda: "model")
    monkeypatch.setattr(container_module, "FsFileRepository", lambda: "files")
    monkeypatch.setattr(container_module, "FfprobeStreamResolution", lambda: "ffprobe-probe")
    monkeypatch.setattr(
        container_module,
        "_create_sqlite_repositories",
        lambda: SimpleNamespace(
            library_index="library-index",
            organize_plan="organize-plan",
            parse_cache="parse-cache",
            title_groups="title-groups",
            title_match="title-match",
            search_tv_library="search-tv-library",
        ),
    )
    monkeypatch.setattr(
        container_module, "make_scan_execute", lambda *args, **kwargs: ("scan", args, kwargs)
    )
    monkeypatch.setattr(container_module, "_create_parse_execute", lambda repos: "parse")
    monkeypatch.setattr(
        container_module, "make_cached_tmdb_hydrate_execute", lambda **kwargs: "hydrate"
    )
    monkeypatch.setattr(container_module, "make_plan_execute", lambda **kwargs: ("plan", kwargs))
    monkeypatch.setattr(
        container_module, "make_apply_execute", lambda *args, **kwargs: ("apply", args, kwargs)
    )
    monkeypatch.setattr(container_module, "make_sync_title_groups_execute", lambda repo: "sync")
    monkeypatch.setattr(
        container_module, "OrganizerPresenterPorts", lambda **kwargs: ("ports", kwargs)
    )
    monkeypatch.setattr(
        container_module, "OrganizerPresenter", lambda **kwargs: ("presenter", kwargs)
    )
    monkeypatch.setattr(container_module, "OrganizerPage", lambda **kwargs: ("page", kwargs))
    monkeypatch.setattr(
        container_module,
        "TmdbPosterAssetSync",
        lambda *args: SimpleNamespace(sync_from_match_result="syncer"),
    )
    monkeypatch.setattr(container_module, "make_match_execute", lambda *args, **kwargs: "match")
    monkeypatch.setattr(container_module, "make_tmdb_search_execute", lambda metadata: "search")
    monkeypatch.setattr(
        container_module, "_create_metadata_provider", lambda api_key, repos: "metadata"
    )
    monkeypatch.setattr(container_module, "default_poster_cache_dir", lambda: "cache-dir")
    monkeypatch.setattr(container_module, "read_tmdb_api_key", lambda: "api-key")
    monkeypatch.setattr(container_module.os, "environ", {})

    page = _create_organizer_page(
        pipeline_model=None,
        progress_dialog=None,
        scan_extensions=(".srt",),
        include_companion_subtitles=False,
    )

    assert page[0] == "page"
    presenter_kwargs = page[1]["presenter"][1]
    scan_execute = presenter_kwargs["scan_execute"]
    assert scan_execute[2]["parse_cache"] == "parse-cache"
    assert scan_execute[2]["resolution_probe"] == "ffprobe-probe"
    assert scan_execute[2]["extensions"] == (".srt",)
    assert presenter_kwargs["plan_execute"][1]["organize_plan"] == "organize-plan"
    assert presenter_kwargs["apply_execute"][2]["library_index"] == "library-index"
    assert presenter_kwargs["apply_execute"][2]["organize_plan"] == "organize-plan"


def test_create_organizer_page_wires_scan_resolution_fallback_for_default_scan(monkeypatch) -> None:
    monkeypatch.setattr(container_module, "PipelineTableModel", lambda: "model")
    monkeypatch.setattr(container_module, "FsFileRepository", lambda: "files")
    monkeypatch.setattr(container_module, "FfprobeStreamResolution", lambda: "ffprobe-probe")
    monkeypatch.setattr(
        container_module,
        "_create_sqlite_repositories",
        lambda: SimpleNamespace(
            library_index="library-index",
            organize_plan="organize-plan",
            parse_cache="parse-cache",
            title_groups="title-groups",
            title_match="title-match",
            search_tv_library="search-tv-library",
        ),
    )
    monkeypatch.setattr(
        container_module, "make_scan_execute", lambda *args, **kwargs: ("scan", args, kwargs)
    )
    monkeypatch.setattr(container_module, "_create_parse_execute", lambda repos: "parse")
    monkeypatch.setattr(
        container_module, "make_cached_tmdb_hydrate_execute", lambda **kwargs: "hydrate"
    )
    monkeypatch.setattr(container_module, "make_plan_execute", lambda **kwargs: ("plan", kwargs))
    monkeypatch.setattr(
        container_module, "make_apply_execute", lambda *args, **kwargs: ("apply", args, kwargs)
    )
    monkeypatch.setattr(container_module, "make_sync_title_groups_execute", lambda repo: "sync")
    monkeypatch.setattr(
        container_module, "OrganizerPresenterPorts", lambda **kwargs: ("ports", kwargs)
    )
    monkeypatch.setattr(
        container_module, "OrganizerPresenter", lambda **kwargs: ("presenter", kwargs)
    )
    monkeypatch.setattr(container_module, "OrganizerPage", lambda **kwargs: ("page", kwargs))
    monkeypatch.setattr(container_module, "read_tmdb_api_key", lambda: "")
    monkeypatch.setattr(container_module.os, "environ", {})

    page = _create_organizer_page(
        pipeline_model=None,
        progress_dialog=None,
        scan_extensions=None,
        include_companion_subtitles=True,
    )

    scan_execute = page[1]["presenter"][1]["scan_execute"]
    assert scan_execute[2]["library_index"] == "library-index"
    assert scan_execute[2]["parse_cache"] == "parse-cache"
    assert scan_execute[2]["resolution_probe"] == "ffprobe-probe"
    assert "extensions" not in scan_execute[2]


def test_app_container_reuses_shared_dependencies_and_closes_connection(monkeypatch) -> None:
    dependencies = SimpleNamespace(
        repos=SimpleNamespace(
            connection=SimpleNamespace(close=lambda: close_calls.append("closed"))
        )
    )
    close_calls: list[str] = []
    build_calls: list[tuple[object, object]] = []
    monkeypatch.setattr(container_module, "_create_organizer_dependencies", lambda: dependencies)
    monkeypatch.setattr(container_module, "_create_tmdb_runtime", lambda repos: "tmdb-runtime")
    monkeypatch.setattr(
        container_module,
        "_build_organizer_page",
        lambda **kwargs: build_calls.append((kwargs["dependencies"], kwargs["tmdb_runtime"]))
        or "page",
    )

    container = AniVaultAppContainer()

    assert container.create_organizer_page() == "page"
    assert container.create_subtitle_organizer_page() == "page"
    assert build_calls == [
        (dependencies, "tmdb-runtime"),
        (dependencies, "tmdb-runtime"),
    ]

    container.close()
    assert close_calls == ["closed"]
