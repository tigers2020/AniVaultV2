from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path

from anivault.adapters.persistence.sqlite.connection import create_connection
from anivault.adapters.persistence.sqlite.sqlite_title_match_repository import (
    SqliteTitleMatchRepository,
    _candidate_from_raw_json,
    _decode_unexpired_candidate,
    _group_match_from_row,
    _match_status_from_string,
    _rank_local_title_hits,
    _rank_title_match,
)
from anivault.contracts.tmdb import TmdbSeriesCandidate


def _candidate(tmdb_id: int, name_ko: str = "Frieren") -> TmdbSeriesCandidate:
    return TmdbSeriesCandidate(
        tmdb_id=tmdb_id,
        name_ko=name_ko,
        original_name="Sousou no Frieren",
        first_air_date="2023-09-29",
        original_language="ja",
        overview="",
        poster_path="/poster.jpg",
        backdrop_path="/backdrop.jpg",
        popularity=1.0,
    )


def test_sqlite_title_match_repository_search_cache_and_series_lookup(tmp_path: Path) -> None:
    conn = create_connection(tmp_path / "tmdb.db")
    repo = SqliteTitleMatchRepository(conn, threading.Lock())
    try:
        repo.put_search_cache(
            "key-1",
            language="ko-KR",
            normalized_query="frieren",
            year_hint=None,
            page=1,
            response_json='{"results":[]}',
            expires_at="2999-01-01T00:00:00Z",
        )
        candidate = _candidate(7)
        repo.upsert_series(
            candidate,
            raw_json=json.dumps(asdict(candidate), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )

        assert repo.get_search_cache_json("key-1") == '{"results":[]}'
        assert repo.get_series_candidate(7) == candidate
        assert repo.find_series_candidates_by_title("Frieren", limit=5) == [candidate]

        repo.invalidate_search("key-1")
        assert repo.get_search_cache_json("key-1") is None
    finally:
        conn.close()


def test_sqlite_title_match_repository_poster_assets_and_helpers(tmp_path: Path) -> None:
    conn = create_connection(tmp_path / "tmdb.db")
    repo = SqliteTitleMatchRepository(conn, threading.Lock())
    try:
        candidate = _candidate(8)
        repo.upsert_series(
            candidate,
            raw_json=json.dumps(asdict(candidate), ensure_ascii=False),
            expires_at="2999-01-01T00:00:00Z",
        )
        poster_file = tmp_path / "poster.jpg"
        poster_file.write_bytes(b"poster")
        repo.save_poster_asset(
            8,
            "poster",
            "/poster.jpg",
            local_path=str(poster_file),
            status="ready",
            verified_at="2026-01-01T00:00:00Z",
        )

        assert repo.get_poster_local_path(8, "poster", "/poster.jpg") == str(poster_file.resolve())
        assert repo.get_poster_local_path(8, "invalid", "/poster.jpg") is None
        assert _match_status_from_string("confirmed") == "confirmed"
        assert _match_status_from_string("bad") is None
        assert _group_match_from_row((1, 8, "confirmed", 0.7)) is not None
        assert _group_match_from_row((1, 8, "bad", 0.7)) is None
        assert _rank_title_match(candidate, "frieren") == 0
        assert (
            _decode_unexpired_candidate(json.dumps(asdict(candidate)), "2999-01-01T00:00:00Z")
            == candidate
        )
        assert _candidate_from_raw_json(json.dumps(asdict(candidate))) == candidate

        ranked = _rank_local_title_hits(
            [(json.dumps(asdict(candidate)), "2999-01-01T00:00:00Z")],
            "frieren",
        )
        assert ranked and ranked[0][2] == candidate
    finally:
        conn.close()
