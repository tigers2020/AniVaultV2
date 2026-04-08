-- 008_tmdb_search_tv_library.sql
-- Permanent local rows aligned with docs/fixtures/tmdb_api/search_tv/_schema.json result_item_keys.

CREATE TABLE tmdb_search_tv_library (
    tmdb_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    adult INTEGER NOT NULL CHECK (adult IN (0, 1)),
    backdrop_path TEXT,
    genre_ids TEXT NOT NULL,
    origin_country TEXT NOT NULL,
    original_language TEXT NOT NULL,
    original_name TEXT NOT NULL,
    overview TEXT NOT NULL,
    popularity REAL NOT NULL,
    poster_path TEXT,
    first_air_date TEXT NOT NULL,
    name TEXT NOT NULL,
    vote_average REAL NOT NULL,
    vote_count INTEGER NOT NULL,
    fetched_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tmdb_id, language)
);

CREATE INDEX idx_tmdb_search_tv_library_language ON tmdb_search_tv_library (language);
