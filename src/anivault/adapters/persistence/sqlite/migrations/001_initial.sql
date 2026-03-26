-- 001_initial.sql
-- Phase 1: schema_migrations, library_roots, scan_sessions, media_files, app_kv
-- AniVault V2 — 문서 기준 초안. 구현 시 동일 내용을 adapters/persistence/sqlite/migrations/ 에 둔다.
-- JSON/시간 컬럼: documents/sqlite_storage/implementation_policy.md

CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE library_roots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_path TEXT NOT NULL UNIQUE,
    path_norm TEXT NOT NULL UNIQUE,
    display_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_scan_at TEXT
);

CREATE TABLE scan_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL,
    scan_kind TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    files_seen INTEGER NOT NULL DEFAULT 0,
    files_added INTEGER NOT NULL DEFAULT 0,
    files_updated INTEGER NOT NULL DEFAULT 0,
    files_removed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (root_id) REFERENCES library_roots (id)
);

CREATE TABLE media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    path_norm TEXT NOT NULL,
    dir_norm TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_stem TEXT NOT NULL,
    extension TEXT NOT NULL,
    media_kind TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    ctime_ns INTEGER,
    inode_hint TEXT,
    content_fingerprint TEXT,
    sidecar_group_key TEXT,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    first_seen_scan_id INTEGER,
    last_seen_scan_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (root_id) REFERENCES library_roots (id),
    FOREIGN KEY (first_seen_scan_id) REFERENCES scan_sessions (id),
    FOREIGN KEY (last_seen_scan_id) REFERENCES scan_sessions (id),
    UNIQUE (root_id, path_norm)
);

CREATE INDEX idx_media_files_root_dir ON media_files (root_id, dir_norm);
CREATE INDEX idx_media_files_root_kind ON media_files (root_id, media_kind);
CREATE INDEX idx_media_files_sidecar ON media_files (root_id, sidecar_group_key);
CREATE INDEX idx_media_files_mtime ON media_files (root_id, mtime_ns);

CREATE TABLE app_kv (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    value_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT
);
