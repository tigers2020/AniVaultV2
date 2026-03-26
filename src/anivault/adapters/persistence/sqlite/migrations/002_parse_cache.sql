-- 002_parse_cache.sql
-- Phase 2: parse_cache (media_file_id PK, ok/error, dto_json NOT NULL)
-- See documents/sqlite_storage/phase_02_parse_cache.md

CREATE TABLE parse_cache (
    media_file_id INTEGER PRIMARY KEY,
    parser_version TEXT NOT NULL,
    parse_status TEXT NOT NULL,
    parse_input_signature TEXT NOT NULL,
    parsed_title TEXT,
    parsed_title_normalized TEXT,
    parsed_year INTEGER,
    season_number INTEGER,
    episode_start INTEGER,
    episode_end INTEGER,
    episode_count INTEGER,
    confidence REAL,
    dto_json TEXT NOT NULL,
    error_code TEXT,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id),
    CHECK (parse_status IN ('ok', 'error'))
);

CREATE INDEX idx_parse_title_norm ON parse_cache (parsed_title_normalized);
