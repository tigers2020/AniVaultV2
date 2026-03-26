-- 004_tmdb_cache.sql
-- Phase 4: TMDB search cache, series row, group–TMDB match
-- See documents/sqlite_storage/phase_04_tmdb_cache.md

CREATE TABLE tmdb_search_cache (
    cache_key TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    year_hint INTEGER,
    page INTEGER NOT NULL DEFAULT 1,
    response_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_tmdb_search_cache_expires ON tmdb_search_cache (expires_at);

CREATE TABLE tmdb_series (
    tmdb_id INTEGER PRIMARY KEY,
    name_ko TEXT NOT NULL DEFAULT '',
    original_name TEXT NOT NULL DEFAULT '',
    poster_path TEXT NOT NULL DEFAULT '',
    raw_json TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE group_tmdb_matches (
    group_id INTEGER PRIMARY KEY,
    tmdb_id INTEGER NOT NULL,
    match_status TEXT NOT NULL,
    match_score REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES title_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (tmdb_id) REFERENCES tmdb_series(tmdb_id),
    CHECK (match_status IN ('auto_matched', 'confirmed', 'rejected'))
);
