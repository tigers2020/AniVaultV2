"""sqlite_tmdb_search_tv_library_repository.py

TmdbSearchTvLibraryRepository SQLite 구현.

Author: Pom Kim
"""

from __future__ import annotations

import sqlite3
from threading import Lock

from anivault.adapters.persistence.sqlite.sqlite_time import utc_now_sqlite_text
from anivault.application.ports.tmdb_search_tv_library_port import TmdbSearchTvLibraryRepository
from anivault.contracts.tmdb import SearchTvLibraryRecord

_UPSERT_SQL = """
INSERT INTO tmdb_search_tv_library (
    tmdb_id, language, adult, backdrop_path, genre_ids, origin_country,
    original_language, original_name, overview, popularity, poster_path,
    first_air_date, name, vote_average, vote_count, fetched_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(tmdb_id, language) DO UPDATE SET
    adult = excluded.adult,
    backdrop_path = excluded.backdrop_path,
    genre_ids = excluded.genre_ids,
    origin_country = excluded.origin_country,
    original_language = excluded.original_language,
    original_name = excluded.original_name,
    overview = excluded.overview,
    popularity = excluded.popularity,
    poster_path = excluded.poster_path,
    first_air_date = excluded.first_air_date,
    name = excluded.name,
    vote_average = excluded.vote_average,
    vote_count = excluded.vote_count,
    fetched_at = excluded.fetched_at,
    updated_at = excluded.updated_at
"""


class SqliteTmdbSearchTvLibraryRepository(TmdbSearchTvLibraryRepository):
    """tests/fixtures/tmdb_api/search_tv 픽스처와 동일 키의 행 저장."""

    def __init__(self, conn: sqlite3.Connection, lock: Lock) -> None:
        self._conn = conn
        self._lock = lock

    def upsert(self, record: SearchTvLibraryRecord) -> None:
        now = utc_now_sqlite_text()
        adult_int = 1 if record.adult else 0
        params = (
            int(record.tmdb_id),
            record.language,
            adult_int,
            record.backdrop_path,
            record.genre_ids_json,
            record.origin_country_json,
            record.original_language,
            record.original_name,
            record.overview,
            float(record.popularity),
            record.poster_path,
            record.first_air_date,
            record.name,
            float(record.vote_average),
            int(record.vote_count),
            now,
            now,
        )
        with self._lock:
            self._conn.execute(_UPSERT_SQL, params)
            self._conn.commit()

    def get(self, tmdb_id: int, language: str) -> SearchTvLibraryRecord | None:
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT tmdb_id, language, adult, backdrop_path, genre_ids, origin_country,
                       original_language, original_name, overview, popularity, poster_path,
                       first_air_date, name, vote_average, vote_count
                FROM tmdb_search_tv_library
                WHERE tmdb_id = ? AND language = ?
                """,
                (int(tmdb_id), language),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return SearchTvLibraryRecord(
            tmdb_id=int(row[0]),
            language=str(row[1]),
            adult=bool(row[2]),
            backdrop_path=str(row[3]) if row[3] is not None else None,
            genre_ids_json=str(row[4]),
            origin_country_json=str(row[5]),
            original_language=str(row[6]),
            original_name=str(row[7]),
            overview=str(row[8]),
            popularity=float(row[9]),
            poster_path=str(row[10]) if row[10] is not None else None,
            first_air_date=str(row[11]),
            name=str(row[12]),
            vote_average=float(row[13]),
            vote_count=int(row[14]),
        )
