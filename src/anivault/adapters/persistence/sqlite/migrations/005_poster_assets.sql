-- 005_poster_assets.sql
-- Phase 5: local poster/backdrop cache metadata
-- See documents/sqlite_storage/phase_05_poster_assets.md

CREATE TABLE poster_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER NOT NULL,
    image_kind TEXT NOT NULL,
    remote_path TEXT NOT NULL,
    local_path TEXT NOT NULL,
    status TEXT NOT NULL,
    verified_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (tmdb_id) REFERENCES tmdb_series(tmdb_id) ON DELETE CASCADE,
    CHECK (image_kind IN ('poster', 'backdrop')),
    CHECK (status IN ('ready', 'stale', 'missing', 'failed')),
    CHECK (remote_path <> ''),
    UNIQUE (tmdb_id, image_kind, remote_path)
);

CREATE INDEX idx_poster_assets_tmdb_kind_status
    ON poster_assets (tmdb_id, image_kind, status);
