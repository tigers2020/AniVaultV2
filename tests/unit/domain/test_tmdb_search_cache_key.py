from __future__ import annotations

from anivault.domain.rules.tmdb_search_cache_key import build_tmdb_search_cache_key


def test_build_tmdb_search_cache_key_normalizes_fields() -> None:
    assert (
        build_tmdb_search_cache_key(" ko-KR ", "  Frieren  ", year=2024, page=0)
        == "tmdb_search:ko-KR:Frieren:2024:1"
    )
    assert (
        build_tmdb_search_cache_key("", "  ", year=None, page=7)
        == "tmdb_search:und::none:7"
    )
