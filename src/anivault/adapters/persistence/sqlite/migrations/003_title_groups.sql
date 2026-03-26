-- 003_title_groups.sql
-- Phase 3: title_groups, title_group_members
-- See documents/sqlite_storage/phase_03_title_groups.md

CREATE TABLE title_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL,
    group_key TEXT NOT NULL,
    group_type TEXT NOT NULL,
    group_confidence REAL,
    canonical_title TEXT,
    canonical_title_normalized TEXT,
    tmdb_series_id INTEGER,
    member_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (root_id) REFERENCES library_roots (id),
    UNIQUE (root_id, group_key),
    CHECK (group_type IN ('parsed_title_norm', 'sidecar')),
    CHECK (member_count >= 0)
);

CREATE TABLE title_group_members (
    group_id INTEGER NOT NULL,
    media_file_id INTEGER NOT NULL,
    member_role TEXT NOT NULL,
    score REAL,
    PRIMARY KEY (group_id, media_file_id),
    FOREIGN KEY (group_id) REFERENCES title_groups (id) ON DELETE CASCADE,
    FOREIGN KEY (media_file_id) REFERENCES media_files (id) ON DELETE CASCADE,
    CHECK (member_role IN ('primary_video', 'subtitle', 'other'))
);

CREATE INDEX idx_title_group_members_media ON title_group_members (media_file_id);
CREATE INDEX idx_title_groups_root ON title_groups (root_id);
