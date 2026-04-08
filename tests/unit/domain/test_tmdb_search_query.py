from __future__ import annotations

from anivault.domain.rules.tmdb_search_query import (
    _strip_trailing_tech_paren,
    compact_compare_key,
    iter_strip_last_word_chain,
    iter_tmdb_search_queries,
    normalize_tmdb_search_query,
)


def test_compact_compare_key_removes_whitespace_and_lowercases() -> None:
    assert compact_compare_key(" My Hero Academia ") == "myheroacademia"


def test_normalize_tmdb_search_query_strips_release_noise() -> None:
    raw = "[SubsPlease] Durarara!! x2 Ten (1080p x264 AAC)"

    assert normalize_tmdb_search_query(raw) == "Durarara x2 Ten"


def test_strip_trailing_tech_paren_keeps_non_tech_suffix() -> None:
    text = "The iDOLM@STER (Shiny Colors)"

    assert _strip_trailing_tech_paren(text) == text


def test_iter_strip_last_word_chain_deduplicates_case_insensitively() -> None:
    assert iter_strip_last_word_chain("Show Show") == ["Show Show", "Show"]


def test_iter_tmdb_search_queries_adds_x2_root_variant() -> None:
    assert iter_tmdb_search_queries("Durarara!! x2 Ten") == ["Durarara x2 Ten", "Durarara"]


def test_iter_tmdb_search_queries_returns_empty_for_blank_value() -> None:
    assert iter_tmdb_search_queries("   ") == []
