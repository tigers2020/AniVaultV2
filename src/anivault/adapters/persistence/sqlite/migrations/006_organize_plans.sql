-- 006_organize_plans.sql
-- Phase 6: organize_plans, organize_plan_items

CREATE TABLE organize_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    root_id INTEGER NOT NULL,
    plan_status TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    fs_log_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (root_id) REFERENCES library_roots (id),
    CHECK (
        plan_status IN (
            'draft',
            'previewed',
            'applied',
            'failed',
            'rolled_back'
        )
    )
);

CREATE INDEX idx_organize_plans_root ON organize_plans (root_id);
CREATE INDEX idx_organize_plans_status ON organize_plans (plan_status);

CREATE TABLE organize_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    src_path_norm TEXT NOT NULL,
    dst_path_norm TEXT NOT NULL,
    operation_kind TEXT NOT NULL,
    status TEXT NOT NULL,
    detail_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES organize_plans (id) ON DELETE CASCADE,
    CHECK (operation_kind IN ('move', 'rename', 'copy', 'link')),
    CHECK (
        status IN (
            'pending',
            'applied',
            'skipped',
            'failed',
            'rolled_back'
        )
    )
);

CREATE INDEX idx_organize_plan_items_plan ON organize_plan_items (plan_id);
CREATE INDEX idx_organize_plan_items_plan_id ON organize_plan_items (plan_id, id);
