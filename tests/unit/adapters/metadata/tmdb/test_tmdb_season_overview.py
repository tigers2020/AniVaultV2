from __future__ import annotations

from types import SimpleNamespace

from anivault.adapters.metadata.tmdb import client as client_module
from anivault.adapters.metadata.tmdb.client import TmdbApiClient
from anivault.adapters.metadata.tmdb.provider import TmdbMetadataProvider


def test_tmdb_metadata_provider_maps_season_overview() -> None:
    season = SimpleNamespace(
        season_number=3,
        episodes=[
            SimpleNamespace(
                episode_number=2,
                name="Episode 2",
                still_url="https://image.tmdb.org/t/p/w300/episode-2.jpg",
            ),
            SimpleNamespace(
                episode_number=1,
                name="Episode 1",
                still_url="https://image.tmdb.org/t/p/w300/episode-1.jpg",
            ),
        ],
    )

    class _Client:
        def tv_show_raw(self, tv_id: int):
            assert tv_id == 100
            return None

        def tv_season_raw(self, tv_id: int, season_number: int):
            assert (tv_id, season_number) == (100, 3)
            return season

    provider = TmdbMetadataProvider(_Client())

    overview = provider.tv_season_overview(100, 3)

    assert overview is not None
    assert overview.season_number == 3
    assert [episode.number for episode in overview.episodes] == [1, 2]
    assert overview.episodes[0].name == "Episode 1"
    assert overview.episodes[0].still_url.endswith("episode-1.jpg")


def test_tmdb_metadata_provider_falls_back_to_last_available_tmdb_season() -> None:
    season = SimpleNamespace(
        season_number=2,
        episodes=[SimpleNamespace(episode_number=1, name="Episode 1")],
    )
    show = SimpleNamespace(
        seasons=[
            SimpleNamespace(season_number=0),
            SimpleNamespace(season_number=1),
            SimpleNamespace(season_number=2),
        ]
    )

    class _Client:
        def tv_show_raw(self, tv_id: int):
            assert tv_id == 91768
            return show

        def tv_season_raw(self, tv_id: int, season_number: int):
            assert (tv_id, season_number) == (91768, 2)
            return season

    provider = TmdbMetadataProvider(_Client())

    overview = provider.tv_season_overview(91768, 4)

    assert overview is not None
    assert overview.season_number == 2


def test_tmdb_api_client_tv_season_raw_returns_none_on_not_found(monkeypatch) -> None:
    client = TmdbApiClient("key")
    monkeypatch.setattr(client_module, "NotFound", RuntimeError)
    monkeypatch.setattr(
        client,
        "_api",
        lambda: SimpleNamespace(
            tv_season=lambda tv_id, season_number: (_ for _ in ()).throw(RuntimeError("missing"))
        ),
    )

    assert client.tv_season_raw(7, 1) is None
